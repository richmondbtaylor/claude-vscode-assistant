# PostgreSQL MCP Server

A production-quality MCP server that lets Claude query your PostgreSQL database. Supports listing tables, describing schemas, and running read-only SELECT queries.

## Phase 1: Research & Planning

### Tool Set

| Tool | Type | Description |
|------|------|-------------|
| `pg_list_schemas` | Read-only | List all non-system schemas in the database |
| `pg_list_tables` | Read-only | List all tables and views in a schema |
| `pg_describe_table` | Read-only | Show columns, types, nullability, defaults, and constraints |
| `pg_run_query` | Read-only | Execute a SELECT query and return rows as JSON |
| `pg_get_table_indexes` | Read-only | List indexes on a table |
| `pg_get_foreign_keys` | Read-only | Show foreign-key relationships for a table |

### Auth Plan

Credentials from env vars: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSSL`.

## Phase 2: Implementation

### Setup

```bash
mkdir postgres-mcp && cd postgres-mcp
npm init -y
npm install @modelcontextprotocol/sdk zod pg
npm install -D typescript @types/node @types/pg ts-node
```

### `src/db.ts` — Database Client with Safety Guards

```typescript
import { Pool, PoolClient } from "pg";

const required = ["PGDATABASE", "PGUSER", "PGPASSWORD"];
for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`Missing required environment variable: ${key}.`);
  }
}

export const pool = new Pool({
  host: process.env.PGHOST ?? "localhost",
  port: parseInt(process.env.PGPORT ?? "5432", 10),
  database: process.env.PGDATABASE,
  user: process.env.PGUSER,
  password: process.env.PGPASSWORD,
  ssl: process.env.PGSSL === "true" ? { rejectUnauthorized: false } : false,
  max: 5,
});

export function assertReadOnly(sql: string): void {
  const normalised = sql.trim().toUpperCase();
  if (!/^(SELECT|WITH)\b/.test(normalised)) {
    throw new Error(`Only SELECT queries are allowed. Got: "${sql.trim().slice(0, 40)}"`);
  }
  for (const kw of ["INSERT","UPDATE","DELETE","DROP","TRUNCATE","ALTER","CREATE","GRANT","REVOKE","COPY"]) {
    if (new RegExp(`\\b${kw}\\b`).test(normalised)) {
      throw new Error(`Forbidden keyword '${kw}' in query. Only read-only SELECT queries are permitted.`);
    }
  }
}

export async function query<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T[]> {
  const client: PoolClient = await pool.connect();
  try {
    await client.query("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY");
    const result = await client.query(sql, params);
    return result.rows as T[];
  } finally {
    client.release();
  }
}
```

### `src/index.ts` — Entry Point

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { query, assertReadOnly } from "./db.js";

const server = new McpServer({ name: "postgres-mcp", version: "1.0.0" });

server.registerTool("pg_list_schemas", {
  description: "List all non-system schemas. Returns schema names and owners.",
  inputSchema: {},
  annotations: { readOnlyHint: true },
}, async () => {
  const rows = await query(
    `SELECT schema_name, schema_owner FROM information_schema.schemata
     WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast')
       AND schema_name NOT LIKE 'pg_temp%' ORDER BY schema_name`
  );
  return { content: [{ type: "text", text: JSON.stringify(rows, null, 2) }], structuredContent: { schemas: rows } };
});

server.registerTool("pg_list_tables", {
  description: "List tables and views in a schema with approximate row counts. Defaults to 'public'.",
  inputSchema: {
    schema: z.string().default("public").describe("Schema name (default: public)"),
    include_views: z.boolean().default(true).describe("Include views in results"),
  },
  annotations: { readOnlyHint: true },
}, async ({ schema, include_views }) => {
  const types = include_views ? ["BASE TABLE","VIEW"] : ["BASE TABLE"];
  const rows = await query(
    `SELECT t.table_name, t.table_type, s.n_live_tup::text AS row_estimate
     FROM information_schema.tables t
     LEFT JOIN pg_stat_user_tables s ON s.schemaname=t.table_schema AND s.relname=t.table_name
     WHERE t.table_schema=$1 AND t.table_type=ANY($2) ORDER BY t.table_type, t.table_name`,
    [schema, types]
  );
  return { content: [{ type: "text", text: JSON.stringify(rows, null, 2) }], structuredContent: { schema, tables: rows } };
});

server.registerTool("pg_describe_table", {
  description: "Describe a table: column names, types, nullability, defaults, and constraints. Use before writing queries.",
  inputSchema: {
    table: z.string().describe("Table name"),
    schema: z.string().default("public").describe("Schema (default: public)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ table, schema }) => {
  const columns = await query(
    `SELECT column_name, data_type, is_nullable, column_default
     FROM information_schema.columns WHERE table_schema=$1 AND table_name=$2 ORDER BY ordinal_position`,
    [schema, table]
  );
  if (!columns.length) return {
    content: [{ type: "text", text: `Table '${schema}.${table}' not found. Use pg_list_tables first.` }],
    isError: true,
  };
  return { content: [{ type: "text", text: JSON.stringify({ schema, table, columns }, null, 2) }], structuredContent: { schema, table, columns } };
});

server.registerTool("pg_run_query", {
  description: "Run a read-only SELECT query. Results capped at 500 rows. INSERT/UPDATE/DELETE/DROP are rejected.",
  inputSchema: {
    sql: z.string().describe("SELECT query. Use $1, $2 ... for parameters."),
    params: z.array(z.union([z.string(), z.number(), z.boolean(), z.null()])).default([]).describe("Parameter values"),
    limit: z.number().min(1).max(500).default(100).describe("Max rows to return (1-500)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ sql, params, limit }) => {
  assertReadOnly(sql);
  const rows = await query(`SELECT * FROM (${sql}) _q LIMIT $${params.length+1}`, [...params, limit]);
  const msg = rows.length === limit ? `Returned ${rows.length} rows (may be truncated).` : `Returned ${rows.length} row(s).`;
  return { content: [{ type: "text", text: `${msg}\n\n${JSON.stringify(rows, null, 2)}` }], structuredContent: { row_count: rows.length, rows } };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Phase 3: Build & Test

```bash
npm run build

PGHOST=localhost PGDATABASE=mydb PGUSER=mcp_readonly PGPASSWORD=secret \
  npx @modelcontextprotocol/inspector node dist/index.js
```

Create a read-only DB role:
```sql
CREATE ROLE mcp_readonly LOGIN PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE mydb TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
```

## Security — Three Layers

1. **DB role**: `mcp_readonly` has only SELECT privileges
2. **`assertReadOnly()`**: Rejects queries not starting with SELECT/WITH; blocks mutation keywords
3. **Session-level**: `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY` enforced per connection
