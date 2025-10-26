"""
Database Query MCP Server.

This module implements an MCP-compliant database query tool using FastMCP.
The tool uses SQLite to simulate database queries with natural language input.
"""

import sqlite3
from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    # Fallback if fastmcp not installed - use mock implementation
    FastMCP = None


# In-memory SQLite database setup
def init_database():
    """
    Initialize an in-memory SQLite database with sample data.

    Creates tables for:
    - accounts: User account creation tracking
    - sales: Revenue and sales data

    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create accounts table
    cursor.execute('''
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            created_date TEXT,
            account_type TEXT,
            status TEXT
        )
    ''')

    # Insert sample account data
    # 42 accounts created last week
    sample_accounts = [
        ('2025-10-18', 'standard', 'active'),
        ('2025-10-18', 'premium', 'active'),
        ('2025-10-19', 'standard', 'active'),
        ('2025-10-19', 'standard', 'active'),
        ('2025-10-19', 'premium', 'active'),
        ('2025-10-20', 'standard', 'active'),
        ('2025-10-20', 'standard', 'active'),
        ('2025-10-20', 'premium', 'active'),
        ('2025-10-20', 'standard', 'active'),
        ('2025-10-21', 'standard', 'active'),
        ('2025-10-21', 'premium', 'active'),
        ('2025-10-21', 'standard', 'active'),
        ('2025-10-21', 'standard', 'active'),
        ('2025-10-21', 'premium', 'active'),
        ('2025-10-22', 'standard', 'active'),
        ('2025-10-22', 'standard', 'active'),
        ('2025-10-22', 'premium', 'active'),
        ('2025-10-22', 'standard', 'active'),
        ('2025-10-22', 'standard', 'active'),
        ('2025-10-23', 'standard', 'active'),
        ('2025-10-23', 'premium', 'active'),
        ('2025-10-23', 'standard', 'active'),
        ('2025-10-23', 'standard', 'active'),
        ('2025-10-23', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'standard', 'active'),
        ('2025-10-24', 'premium', 'active'),
    ]

    cursor.executemany(
        'INSERT INTO accounts (created_date, account_type, status) VALUES (?, ?, ?)',
        sample_accounts
    )

    # Create sales table
    cursor.execute('''
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            sale_date TEXT,
            amount REAL,
            quarter TEXT,
            month TEXT
        )
    ''')

    # Insert sample sales data
    # Total Q3 revenue: $1.2M
    sample_sales = [
        ('2025-07-15', 250000.00, 'Q3', 'July'),
        ('2025-07-20', 150000.00, 'Q3', 'July'),
        ('2025-08-10', 300000.00, 'Q3', 'August'),
        ('2025-08-25', 200000.00, 'Q3', 'August'),
        ('2025-09-05', 180000.00, 'Q3', 'September'),
        ('2025-09-18', 120000.00, 'Q3', 'September'),
    ]

    cursor.executemany(
        'INSERT INTO sales (sale_date, amount, quarter, month) VALUES (?, ?, ?, ?)',
        sample_sales
    )

    conn.commit()
    return conn


# Global database connection
DB_CONN = init_database()


def query_database(query: str) -> str:
    """
    Process natural language query and execute against SQLite database.

    Args:
        query: Natural language query string

    Returns:
        Human-readable string summary of query results

    Examples:
        >>> query_database("How many accounts were created?")
        '42 new accounts were created last week.'

        >>> query_database("What is the revenue for Q3?")
        'Total sales revenue for Q3 is $1.2M.'
    """
    if not query or not isinstance(query, str):
        return "Invalid query. Please provide a valid question."

    query_lower = query.lower()

    try:
        cursor = DB_CONN.cursor()

        # Parse query intent and execute appropriate SQL

        # Account queries
        if "account" in query_lower:
            if "how many" in query_lower or "created" in query_lower:
                # Count accounts created last week
                cursor.execute('''
                    SELECT COUNT(*) FROM accounts
                    WHERE created_date >= date('2025-10-18')
                ''')
                count = cursor.fetchone()[0]
                return f"{count} new accounts were created last week."

            elif "premium" in query_lower:
                # Count premium accounts
                cursor.execute('''
                    SELECT COUNT(*) FROM accounts
                    WHERE account_type = 'premium'
                ''')
                count = cursor.fetchone()[0]
                return f"There are {count} premium accounts."

            else:
                # Total accounts
                cursor.execute('SELECT COUNT(*) FROM accounts')
                count = cursor.fetchone()[0]
                return f"There are {count} total accounts."

        # Sales/revenue queries
        elif "sales" in query_lower or "revenue" in query_lower:
            if "q3" in query_lower or "quarter" in query_lower:
                # Q3 revenue
                cursor.execute('''
                    SELECT SUM(amount) FROM sales
                    WHERE quarter = 'Q3'
                ''')
                total = cursor.fetchone()[0]
                # Format as millions
                total_millions = total / 1_000_000
                return f"Total sales revenue for Q3 is ${total_millions:.1f}M."

            elif "september" in query_lower:
                # September revenue
                cursor.execute('''
                    SELECT SUM(amount) FROM sales
                    WHERE month = 'September'
                ''')
                total = cursor.fetchone()[0]
                return f"Sales revenue for September is ${total:,.2f}."

            elif "august" in query_lower:
                # August revenue
                cursor.execute('''
                    SELECT SUM(amount) FROM sales
                    WHERE month = 'August'
                ''')
                total = cursor.fetchone()[0]
                return f"Sales revenue for August is ${total:,.2f}."

            else:
                # Total revenue
                cursor.execute('SELECT SUM(amount) FROM sales')
                total = cursor.fetchone()[0]
                total_millions = total / 1_000_000
                return f"Total sales revenue is ${total_millions:.1f}M."

        else:
            # No matching query pattern
            return "No data available for this query."

    except Exception as e:
        return f"Database error: {str(e)}"


# Create FastMCP server if available
if FastMCP is not None:
    mcp = FastMCP("DatabaseQueryServer")

    @mcp.tool(
        name="database_query",
        description="Execute natural language queries against the database to retrieve metrics and data"
    )
    def execute_database_query(query: str) -> str:
        """
        Execute a natural language query against the database.

        This tool converts natural language questions into SQL queries
        and executes them against a SQLite database containing business
        metrics like account creation and sales revenue.

        Args:
            query: Natural language question about database metrics

        Returns:
            Human-readable summary of query results

        Examples:
            Query: "How many accounts were created last week?"
            Result: "42 new accounts were created last week."

            Query: "What is the revenue for Q3?"
            Result: "Total sales revenue for Q3 is $1.2M."
        """
        return query_database(query)
else:
    # Fallback if FastMCP not available
    mcp = None


class DatabaseTool:
    """
    Database query tool with callable interface.

    Implements __call__ to match OpenAI tool-calling semantics.
    Provides synchronous access to the MCP database query tool.
    """

    def __init__(self):
        """Initialize the database tool."""
        self.mcp_server = mcp
        self.db_conn = DB_CONN

    def __call__(self, query: str) -> str:
        """
        Execute database query.

        Args:
            query: Natural language query string

        Returns:
            Human-readable query results

        Examples:
            >>> tool = DatabaseTool()
            >>> tool("How many accounts were created?")
            '42 new accounts were created last week.'
        """
        return query_database(query)


def create_database_tool() -> DatabaseTool:
    """
    Factory function to create a DatabaseTool instance.

    Returns:
        Configured DatabaseTool instance

    Examples:
        >>> tool = create_database_tool()
        >>> result = tool("How many accounts?")
        >>> "42" in result
        True
    """
    return DatabaseTool()
