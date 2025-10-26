# Scalekit OAuth Example

Demonstrates FastMCP server protection with Scalekit OAuth.

## Setup

### 1. Configure MCP server in Scalekit environment

**Create a Scalekit Account**:

- Go to [Scalekit Dashboard](https://app.scalekit.com/)
- Navigate to **Developers** → **Settings**
- Copy your Environment URL, Client ID, and Client Secret

**Register Your MCP Server**:

- Go to **MCP Servers** → **Create New Server**
- Fill in your MCP server details
- Note the **Resource ID** (e.g., `res_123`)

Create a `.env` file:

```bash
# Required Scalekit credentials
SCALEKIT_ENVIRONMENT_URL=<YOUR_APP_ENVIRONMENT_URL>
SCALEKIT_CLIENT_ID=<YOUR_APP_CLIENT_ID> # skc_7008EXAMPLE46
SCALEKIT_RESOURCE_ID=<YOUR_APP_RESOURCE_ID> # res_926EXAMPLE5878
MCP_URL=http://localhost:8000/mcp
```

### 2. Run the Example

Start the server:

```bash
# From this directory
uv run python server.py
```

The server will start on `http://localhost:8000/mcp` with Scalekit OAuth authentication enabled.

Test with client:

```bash
uv run python client.py
```

The `client.py` will:

1. Attempt to connect to the server
2. Detect that OAuth authentication is required
3. Open a browser for Scalekit authentication
4. Complete the OAuth flow and connect to the server
5. Demonstrate calling authenticated tools
