# PostgreSQL MCP Server (Haiku + Skill)

## Phase 1: Research & Planning

**Tool Set (read-only, pg_ prefix):**
1. `pg_list_tables` — List all tables in a schema with row counts
2. `pg_describe_table` — Describe columns, types, nullability, constraints
3. `pg_execute_query` — Run a read-only SELECT query safely

**Auth:** `DATABASE_URL` or individual `PGHOST`/`PGUSER`/`PGPASSWORD`/`PGDATABASE` env vars

## Phase 2: Implementation

**Setup:**
```bash
mkdir postgres-mcp && cd postgres-mcp
npm init -y
npm install @modelcontextprotocol/sdk zod pg
npm install -D typescript @types/node @types/pg
```

**Tools with Zod schemas:**
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { Pool } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const server = new McpServer({ name: "postgres-mcp", version: "1.0.0" });

server.registerTool("pg_list_tables", {
  description: "List all tables in the database. Returns table name, schema, and approximate row count.",
  inputSchema: {
    schema: z.string().default("public").describe("Schema name to list tables from (default: public)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ schema }) => {
  const rows = await pool.query(
    `SELECT table_name, table_type FROM information_schema.tables
     WHERE table_schema = $1 ORDER BY table_name`,
    [schema]
  );
  return {
    content: [{ type: "text", text: JSON.stringify(rows.rows, null, 2) }],
    structuredContent: { schema, tables: rows.rows },
  };
});

server.registerTool("pg_describe_table", {
  description: "Describe a table schema: column names, data types, nullability, and defaults. Use before writing queries.",
  inputSchema: {
    table: z.string().describe("Table name to describe"),
    schema: z.string().default("public").describe("Schema name (default: public)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ table, schema }) => {
  const rows = await pool.query(
    `SELECT column_name, data_type, is_nullable, column_default
     FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2
     ORDER BY ordinal_position`,
    [schema, table]
  );
  if (!rows.rows.length) {
    return {
      content: [{ type: "text", text: `Table '${schema}.${table}' not found. Use pg_list_tables to see available tables.` }],
      isError: true,
    };
  }
  return {
    content: [{ type: "text", text: JSON.stringify(rows.rows, null, 2) }],
    structuredContent: { schema, table, columns: rows.rows },
  };
});

server.registerTool("pg_execute_query", {
  description: "Execute a read-only SELECT query. Only SELECT statements are allowed — INSERT/UPDATE/DELETE/DROP are rejected.",
  inputSchema: {
    sql: z.string().describe("SQL SELECT query to execute"),
    limit: z.number().min(1).max(500).default(100).describe("Maximum rows to return (1-500)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ sql, limit }) => {
  const upper = sql.trim().toUpperCase();
  if (!upper.startsWith("SELECT")) {
    throw new Error(`Only SELECT queries allowed. Received: '${sql.trim().slice(0, 40)}'`);
  }
  const rows = await pool.query(`SELECT * FROM (${sql}) q LIMIT $1`, [limit]);
  return {
    content: [{ type: "text", text: JSON.stringify(rows.rows, null, 2) }],
    structuredContent: { row_count: rows.rows.length, rows: rows.rows },
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Phase 3: Build & Test

```bash
npm run build
DATABASE_URL=postgresql://user:pass@localhost/mydb \
  npx @modelcontextprotocol/inspector node dist/index.js
```

## Phase 4: Evaluations (sample)

```xml
<evaluation>
  <qa_pair>
    <question>List all tables in the public schema. How many are there?</question>
    <answer>N (from actual database)</answer>
  </qa_pair>
</evaluation>
```

*(Note: Haiku with skill — agent produced structured 4-phase response, 3 tools with pg_ prefix, Zod schemas, read-only safety, hit Write permission denial)*
