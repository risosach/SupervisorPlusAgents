# Securing MCP Tools with Azure AD On-Behalf-Of (OBO) | by Saima Khan | Sep, 2025 | Medium
What is the OBO Pattern?
------------------------

The **On-Behalf-Of (OBO)** pattern is a delegated authentication flow defined by Microsoft that allows a service to call downstream APIs using a user’s identity.

In the OBO flow:

1.  The user authenticates and receives an access token.
2.  The server (a confidential client) receives this token and exchanges it for another token **targeted at the downstream resource**.
3.  The tool uses that new token to safely access external APIs **on behalf of the user**.

📖 [Microsoft Docs: OAuth 2.0 On-Behalf-Of flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow)

This pattern is particularly useful when your MCP tools need to access APIs such as:

*   Azure DevOps (e.g., create work items, read PRs)
*   Microsoft Graph (e.g., fetch user profile or calendar)
*   Azure Cognitive Search (e.g., query secured indexes)

While OBO is commonly used with Microsoft services (like the ones above), the core concept **securely delegating access to a downstream API using an upstream token** can be applied to **any API** that supports OAuth2 and scopes-based access control.

The only requirement is that:

*   The downstream service must trust the identity provider issuing the exchanged token.
*   The application (confidential client) must be registered and authorized to request tokens for that downstream API.

Why OBO Matters in MCP
----------------------

In the previous post, we focused on **App Role-based filtering** where tools are either shown or hidden based on a user���s assigned role. That helps avoid accidental exposure to destructive or sensitive tools.

However, this visibility control alone isn’t always enough. What if a tool is correctly exposed but calls an **external system that requires user-specific permissions**?

> Without OBO, even users with minimal roles might be able to invoke tools that call protected APIs — potentially modifying, deleting, or accessing data they shouldn’t. This is especially risky when:

*   The downstream API (e.g., Azure DevOps, Cognitive Search) exposes privileged operations
*   MCP tools execute using a shared static token (e.g., a Service Principle, Service Credentials) that lacks user context

This is where the **On-Behalf-Of (OBO)** pattern plays a critical role. Instead of granting blanket access via a shared service identity, OBO ensures that:

*   Each API call happens in the **true context of the user**
*   The external system enforces **RBAC, ACLs, or policy checks** based on the user’s actual permissions
*   Tools remain reusable, but execution is dynamically controlled

Architecture Overview
---------------------

Here’s a high-level view of how the On-Behalf-Of flow fits into the MCP architecture:

### OBO Flow: Step-by-Step

Below is a sequence diagram representing the OBO token flow, including token caching, user interaction, and delegated API access:

Press enter or click to view image in full size

Here’s how the OBO flow plays out in the MCP context:

1.  The user logs into the MCP client and obtains an access token scoped for the MCP Server. This requires the appropriate app registrations in Entra ID.
2.  The MCP Server validates the incoming token using FastMCP’s built-in token verification, ensuring it was issued by Entra ID and has the correct audience.
3.  When the user invokes a tool (e.g., to interact with Azure Cognitive Search), the agent routes the request to the MCP tool handler.
4.  The tool retrieves the original user token (using a helper in FastMCP), then performs an OBO token exchange to get a new token scoped for the external API.
5.  The tool uses this new token to call the downstream API on behalf of the user and returns the result back through the MCP server to the client.

This ensures that downstream APIs receive user-specific tokens, allowing them to enforce granular access policies.

Setting Up OBO in Azure
-----------------------

We are building an MCP Server that exposes one tool that queries **Microsoft Graph access** to list SharePoint sites accessible by the signed-in user. You need to configure **two app registrations** in Entra ID to support the OBO flow.

### Frontend App Registration (Client CLI / Interface)

This app is responsible for acquiring the user token to access the MCP Server.

I will use the **confidential client flow**, with a browser-based login and redirect to obtain the user’s token using the authorization code grant.

Steps:

1.  **Create another App Registration** (e.g., `FastMCP-OBO-Client`)
2.  Go to **Certificates & secrets, a**dd a client secret
3.  Go to **API Permissions**:

*   Add **delegated permission** to access the backend API (`access_as_user` scope)

4\. Under **Authentication,** add a **Redirect URI** (e.g., `http://localhost:8100/auth/callback`) for use with Authorization Code Flow. This must match the one used in your client script. You can keep **public client flows** disabled.

### Backend App Registration (MCP Server)

This app represents your FastMCP Server. It must be registered as a **confidential client**, since it will perform the token exchange on behalf of the user.

Steps:

1.  **Create an App Registration** (e.g., `FastMCP-OBO-Server`)
2.  Go to **Expose an API**:

*   Set an Application ID URI (e.g., `api://<client-id>`)
*   Add a custom scope — name it `access_as_user` (used by the client to request delegated access)

3\. Go to **API Permissions**:

*   Add delegated permissions to **Microsoft Graph** → `Sites.Read.All`

4\. Go to **Certificates & secrets**:

*   Generate a **client secret** — this is required for the MCP Server to authenticate itself during the OBO token exchange flow

### 🔄 Link the Two Registrations

In the **backend app registration**:

*   Under **Expose an API** → **Authorized client applications**, add the **client ID** of the frontend app. This authorizes the frontend to call the backend using the `access_as_user` scope.

Sample Code for OBO in MCP Tool
-------------------------------

The following MCP server implementation includes a tool that uses the OBO flow to query Microsoft Graph and check whether a user has access to a given SharePoint site.

This is built using the FastMCP Python SDK. The server includes:

*   **Tier-1 security**: App Role-based filtering using a custom `AuthorizationMiddleware`, imported from the `shared` package — previously explained in [this article](https://medium.com/@khansaima/securing-mcp-servers-with-azure-ad-and-jwt-based-role-authorization-d8c8aeadb7f5). For this to work, ensure that app roles are defined in your backend app registration and assigned to users accordingly.
*   **Tier-2 security**: Runtime access enforcement using the **On-Behalf-Of (OBO)** pattern to securely access Microsoft Graph with delegated user context

_Below is the full server file with inline comments_

```
#!/usr/bin/env python3
"""
FastMCP Server with Entra ID Authentication and OBO flow for Microsoft Graph
"""
import logging
import os
import jwt
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.auth.providers.jwt import JWTVerifier  # Used for Tier-1 JWT token validation
from shared.middleware.authorization_middleware import AuthorizationMiddleware  # Role-based filtering
from fastmcp.server.dependencies import get_access_token, AccessToken
load_dotenv()
# Server-level configuration
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
MIDDLEWARE_ENABLED = os.getenv("MIDDLEWARE_ENABLED", "false").lower() == "true"
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
OBO_CLIENT_ID = os.getenv("OBO_CLIENT_ID")
OBO_CLIENT_SECRET = os.getenv("OBO_CLIENT_SECRET")
ISSUER = os.getenv("ISSUER")
if AUTH_ENABLED:
    bearer_auth = JWTVerifier(
            jwks_uri=f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys",
            issuer=ISSUER,
        )
    mcp = FastMCP("MCP Server with AUTH", auth=bearer_auth)
    mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=True, transform_errors=True))
    if MIDDLEWARE_ENABLED:
        mcp.add_middleware(AuthorizationMiddleware(auth_context))
else:
    mcp = FastMCP("MCP Server without Auth")
    mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=True, transform_errors=True))
# ========== OBO Exchange Logic ==========
async def exchange_token(original_token: str, scope: str) -> dict:
    obo_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": OBO_CLIENT_ID,
        "client_secret": OBO_CLIENT_SECRET,
        "assertion": original_token,
        "scope": scope,
        "requested_token_use": "on_behalf_of",
    }
    try:
        response = requests.post(obo_url, data=data)
        if response.status_code == 200:
            return {"success": True, "access_token": response.json()
["access_token"]}
        return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}
# ========== TOOL IMPLEMENTATION ==========  
@mcp.tool(tags={"write"})
async def test_write_tool() -> dict:
    ## Explicit Tool level validation using app roles
    if AUTH_ENABLED:
        access_token: AccessToken = get_access_token()
        token_info = jwt.decode(access_token.token, options={"verify_signature": False})
        role_access = any(
            role
            for role in token_info.get("roles", [])
            if role in ("Task.All", "Task.Write")
        )
        if not role_access:
            return {
                "error": "Access denied. You do not have permission to call this tool."
            }
    return {"message": "This is a write test tool response"}
@mcp.tool(tags={"read"})
async def check_sharepoint_site_access(site_name: str) -> str:
    """
    Check if the user has access to a specific SharePoint site using Microsoft Graph.
    """
    if not AUTH_ENABLED:
        return "Authentication must be enabled."
    # Step 1: Get user token from request
    access_token: AccessToken = get_access_token()
    original_token = access_token.token
    # Step 2: Perform OBO token exchange
    graph_result = await exchange_token(
        original_token, scope="https://graph.microsoft.com/.default"
    )
    if not graph_result["success"]:
        return "Token exchange failed."
    obo_token = graph_result["access_token"]
    url = f"https://graph.microsoft.com/v1.0/sites/riotinto.sharepoint.com:/sites/{site_name}"
    headers = {"Authorization": f"Bearer {obo_token}"}
    # Step 3: Make Graph API call
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return f"✅ Access granted to site: {site_name}"
    elif response.status_code in [403, 404]:
        return f"❌ Access denied to site: {site_name}"
    else:
        return f"⚠️ Error: {response.status_code}"
# ========== SERVER ENTRYPOINT ==========
def main():
    try:
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8400,
        )
    except Exception as e:
        logging.error(f"Server failed to start: {e}")
if __name__ == "__main__":
    main()
```


I have also included the corresponding **client implementation** which:

*   Authenticates the user using Authorization Code Flow via `ConfidentialClientApplication`
*   Starts a local HTTP server to receive the auth code
*   Acquires a token for the backend API (`access_as_user` scope)
*   Sends that token while invoking tools, including the Graph-connected one

_Below is full client code with browser login and tool_

```
import asyncio
import json
import logging
import os
import jwt
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import webbrowser
from dotenv import load_dotenv
from msal import ConfidentialClientApplication, SerializableTokenCache
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-client-confidential")
load_dotenv("../servers/.env")
# =========================
# CONFIGURATION
# =========================
TENANT_ID = os.getenv("TENANT_ID", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()
API_A_SCOPE = os.getenv("API_A_SCOPE", "").strip()  # e.g., api://<OBO_CLIENT_ID>/access_as_user
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8100/auth/callback").strip()
MCP_URL = os.getenv("MCP_URL", "http://localhost:8400/mcp/").strip()
CACHE_PATH = os.getenv("MSAL_CACHE_PATH", ".msal_token_cache.bin").strip()
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
# =========================
# LOCAL HTTP LISTENER
# =========================
class _AuthCodeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        self.server.auth_code = params.get("code", [None])
[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"You can now close this window.")
def _start_local_server(port):
    server = HTTPServer(("localhost", port), _AuthCodeHandler)
    server.auth_code = None
    return server
def decode_token_info(token: str) -> dict:
    """
    Decode token to show basic info (without verification)
    """
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return {
            "audience": decoded.get("aud"),
            "issuer": decoded.get("iss"),
            "subject": decoded.get("sub"),
            "user_id": decoded.get("oid"),
            "preferred_username": decoded.get("upn"),
            "name": decoded.get("name"),
            "scopes": decoded.get("scp"),
            "expires": decoded.get("exp"),
            "roles": decoded.get("roles"),
            "app_id": decoded.get("appid"),
        }
    except Exception as e:
        return {"error": str(e)}
# =========================
# TOKEN ACQUISITION
# =========================
def acquire_user_token():
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, API_A_SCOPE]):
        raise RuntimeError("Missing required environment variables.")
    scopes = [API_A_SCOPE]
    cache = SerializableTokenCache()
    if os.path.exists(CACHE_PATH):
        try:
            cache.deserialize(open(CACHE_PATH, "r").read())
        except Exception:
            logger.warning("Failed to deserialize cache. Starting fresh.")
    app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
        token_cache=cache,
    )
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
    if not result:
        # Auth Code Flow
        port = urlparse(REDIRECT_URI).port or 8100
        server = _start_local_server(port)
        auth_url = app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=REDIRECT_URI,
            prompt="select_account",
        )
        logger.info(f"Open your browser: {auth_url}")
        webbrowser.open(auth_url)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        thread.join(timeout=300)
        if not server.auth_code:
            raise RuntimeError("Auth code not received.")
        result = app.acquire_token_by_authorization_code(
            code=server.auth_code,
            scopes=scopes,
            redirect_uri=REDIRECT_URI,
        )
    access_token = result.get("access_token")
    if not access_token:
        raise RuntimeError(f"Token acquisition failed: {json.dumps(result, indent=2)}")
    # Optional: print user details
    id_token_claims = result.get("id_token_claims", {})
    id_token = id_token_claims if id_token_claims else decode_token_info(access_token)
    logger.info(
        f"User signed in: {id_token.get('name')} ({id_token.get('preferred_username')})"
    )
    with open(CACHE_PATH, "w") as f:
        f.write(cache.serialize())
    return access_token
# =========================
# MCP CLIENT
# =========================
async def run_client():
    headers = None
    if AUTH_ENABLED:
        token = acquire_user_token()
        headers = {"Authorization": f"Bearer {token}"}
    client = MCPClient(transport=StreamableHttpTransport(url=MCP_URL, headers=headers))
    try:
        logger.info("Connecting to MCP server...")
        logger.info(f"Client Connection: {client.is_connected()}")
        async with client:
            tools = await client.list_tools()
            logger.info(f"Found {len(tools)} tools")
            result = await client.call_tool("test_write_tool")
            logger.info(f"Test Write Tool Response: {result}")
            # OBO Example
            graph_result = await client.call_tool(
                "check_sharepoint_site_access", {"site_name": "test-site"}
            )
            logger.info(graph_result)
    except Exception as e:
        logger.error(f"Client error: {e}")
if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        sys.exit(0)
```


Best Practices
--------------

*   **Secure Your Secrets**  
    Use Azure Key Vault or a secure secrets manager to store `client_id` and `client_secret`. Avoid hardcoding credentials in your codebase.
*   **Use Short-Lived Tokens**  
    OBO tokens are short-lived by design. Avoid caching them long-term; perform token exchange per tool execution.
*   **Apply Principle of Least Privilege**  
    Only request the delegated Microsoft Graph permissions your tools require. For example, `Sites.Read.All` for SharePoint access. Avoid over-permissioning your app.
*   **Validate Tokens Server-Side**  
    Always validate tokens for `issuer`, `audience`, and `expiration`. FastMCP’s built-in bearer auth provider takes care of this when configured properly.
*   **Log Tool Usage and API Calls**  
    For audit and traceability, log who invoked each tool and whether external APIs were called especially for write/delete actions.

Summary
-------

*   **Tier-1 Security (App Roles + Token Verification)**  
    Controls _what tools_ a user can see and invoke based on assigned roles.
*   **Tier-2 Security (OBO Pattern)**  
    Ensures the tool’s _runtime actions_ reflect the user’s real permissions on downstream systems like Microsoft Graph or Azure DevOps.

This layered security model brings **visibility control**, **runtime enforcement**, and **traceability** — making your mcp tools more secure and enterprise-ready.