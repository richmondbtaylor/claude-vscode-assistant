# Building an MCP Server for PostgreSQL

## Overview

An MCP server for PostgreSQL lets Claude list tables, inspect schemas, and run SELECT queries against your database. Here's how to build it.

## Prerequisites

- Node.js 18+ or Python 3.10+
- PostgreSQL database with connection credentials
- `@modelcontextprotocol/sdk` (TypeScript) or `mcp` (Python)

## TypeScript Implementation

```bash
mkdir postgres-mcp && cd postgres-mcp
npm init -y
npm install @modelcontextprotocol/sdk pg
npm install -D typescript @types/node @types/pg
```

### `src/index.ts`

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const server = new Server({
  name: "postgres-mcp",
  version: "1.0.0",
}, {
  capabilities: { tools: {} }
});

server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "list_tables",
      description: "List all tables in the database",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "describe_table",
      description: "Get column info for a table",
      inputSchema: {
        type: "object",
        properties: {
          table_name: { type: "string", description: "Name of the table" }
        },
        required: ["table_name"]
      }
    },
    {
      name: "run_query",
      description: "Run a SELECT query",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "SQL SELECT query to run" }
        },
        required: ["query"]
      }
    }
  ]
}));

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "list_tables") {
    const result = await pool.query(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    );
    return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
  }

  if (name === "describe_table") {
    const result = await pool.query(
      "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1",
      [args.table_name]
    );
    return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
  }

  if (name === "run_query") {
    // Basic safety: only allow SELECT
    if (!args.query.trim().toUpperCase().startsWith("SELECT")) {
      throw new Error("Only SELECT queries are allowed");
    }
    const result = await pool.query(args.query);
    return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "postgres": {
      "command": "node",
      "args": ["/path/to/postgres-mcp/dist/index.js"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/mydb"
      }
    }
  }
}
```

## Python Alternative

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import psycopg2, os

app = Server("postgres-mcp")
conn = psycopg2.connect(os.environ["DATABASE_URL"])

@app.list_tools()
async def list_tools():
    return [...]  # same 3 tools

@app.call_tool()
async def call_tool(name, arguments):
    # implementation
    pass

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
```

*(Note: agent hit permission denial — response reconstructed from task notification summary)*
