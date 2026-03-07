# PostgreSQL MCP Server (No Skill Baseline - Haiku)

## Architecture

MCP server bridges Claude and PostgreSQL using stdio transport.

## Three Main Tools

1. `list_tables` - Show all tables in the database
2. `describe_table` - Get schema information for a specific table
3. `execute_query` - Run read-only SELECT queries safely

## Core Implementation

**`database.py`**: Connection management, table listing, schema description, and safe SELECT query execution

**`handlers.py`**: MCP tool handlers for each operation

**`server.py`**: Main MCP server with tool definitions

**`pyproject.toml`**: Dependencies and project configuration

## Security Features

- Parameterized queries to prevent SQL injection
- Query validation (reject dangerous keywords)
- Read-only enforcement
- Environment-based credentials

*(Note: Haiku baseline — Python-first approach, 3 tools named without prefix, no Zod, no TypeScript, no structuredContent, no error message specifics)*
