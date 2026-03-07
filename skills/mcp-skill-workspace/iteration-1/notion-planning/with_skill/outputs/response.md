# Building an MCP Server for the Notion API

## Phase 1: Research & Planning

### Load Documentation

Fetch these before implementing:
- MCP intro: `https://modelcontextprotocol.io/introduction.md`
- TypeScript SDK: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- Notion API: `https://developers.notion.com/reference/intro`

### Notion API Essentials

- **Base URL**: `https://api.notion.com/v1/`
- **Auth**: `Authorization: Bearer <NOTION_API_KEY>` header
- **Version**: `Notion-Version: 2022-06-28` header required
- **Rate limits**: 3 requests/second average; 429 = back off
- **Pagination**: `start_cursor` + `has_more` + `next_cursor`
- **Sharing**: Pages/DBs must be explicitly shared with your integration

### Tool Inventory

| Priority | Tool | Annotation |
|----------|------|------------|
| 1 | `notion_search` | `readOnlyHint: true` |
| 1 | `notion_list_databases` | `readOnlyHint: true` |
| 1 | `notion_get_database` | `readOnlyHint: true` |
| 1 | `notion_query_database` | `readOnlyHint: true` |
| 1 | `notion_get_page` | `readOnlyHint: true` |
| 1 | `notion_get_page_content` | `readOnlyHint: true` |
| 2 | `notion_create_page` | `destructiveHint: false, idempotentHint: false` |
| 2 | `notion_update_page` | `idempotentHint: true` |

## Phase 2: Implementation

### Setup

```bash
mkdir notion-mcp && cd notion-mcp
npm init -y
npm install @modelcontextprotocol/sdk @notionhq/client zod
npm install -D typescript @types/node ts-node
```

### `src/notion-client.ts` — Auth & Shared Utilities

```typescript
import { Client } from "@notionhq/client";

if (!process.env.NOTION_API_KEY) {
  throw new Error("NOTION_API_KEY environment variable is required.");
}

export const notion = new Client({ auth: process.env.NOTION_API_KEY });

export function notionError(err: unknown, context: string): never {
  const msg = err instanceof Error ? err.message : String(err);
  if (msg.includes("Could not find")) {
    throw new Error(`${context}: Not found. Make sure the page/database is shared with your integration.`);
  }
  if (msg.includes("Unauthorized")) {
    throw new Error(`${context}: Unauthorized. Check NOTION_API_KEY is valid.`);
  }
  throw new Error(`${context}: ${msg}`);
}

export async function paginate<T>(
  fn: (cursor?: string) => Promise<{ results: T[]; has_more: boolean; next_cursor: string | null }>,
  maxResults = 100
): Promise<T[]> {
  const results: T[] = [];
  let cursor: string | undefined;
  while (results.length < maxResults) {
    const page = await fn(cursor);
    results.push(...page.results);
    if (!page.has_more || !page.next_cursor) break;
    cursor = page.next_cursor;
  }
  return results.slice(0, maxResults);
}
```

### `src/index.ts` — Tools

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { notion, notionError, paginate } from "./notion-client.js";

const server = new McpServer({ name: "notion-mcp", version: "1.0.0" });

server.registerTool("notion_list_databases", {
  description: "List all Notion databases your integration has access to. Returns database IDs, titles, and property schemas.",
  inputSchema: {
    max_results: z.number().min(1).max(100).default(50).describe("Maximum databases to return (1-100)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ max_results }) => {
  try {
    const dbs = await paginate(
      (cursor) => notion.search({ filter: { object: "database" }, start_cursor: cursor, page_size: 100 }) as any,
      max_results
    );
    const result = { count: dbs.length, databases: dbs.map((db: any) => ({
      id: db.id,
      title: db.title?.[0]?.plain_text ?? "(untitled)",
      properties: Object.keys(db.properties ?? {}),
      url: db.url,
    }))};
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], structuredContent: result };
  } catch (err) { notionError(err, "notion_list_databases"); }
});

server.registerTool("notion_query_database", {
  description: "Query pages in a Notion database with optional filters. Returns page IDs, titles, and all property values.",
  inputSchema: {
    database_id: z.string().describe("Notion database ID (32-char hex or UUID format from the URL)"),
    filter: z.string().optional().describe("JSON filter object per Notion API spec, e.g. {\"property\":\"Status\",\"select\":{\"equals\":\"Done\"}}"),
    max_results: z.number().min(1).max(200).default(50).describe("Max pages to return (1-200)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ database_id, filter, max_results }) => {
  try {
    const filterObj = filter ? JSON.parse(filter) : undefined;
    const pages = await paginate(
      (cursor) => notion.databases.query({ database_id, filter: filterObj, start_cursor: cursor, page_size: 100 }) as any,
      max_results
    );
    const result = { count: pages.length, pages: pages.map((p: any) => ({ id: p.id, properties: p.properties, url: p.url })) };
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], structuredContent: result };
  } catch (err) { notionError(err, "notion_query_database"); }
});

server.registerTool("notion_get_page", {
  description: "Get a Notion page's metadata and properties (title, status, dates, etc.). Does not include page body content — use notion_get_page_content for that.",
  inputSchema: {
    page_id: z.string().describe("Notion page ID from the URL"),
  },
  annotations: { readOnlyHint: true },
}, async ({ page_id }) => {
  try {
    const page = await notion.pages.retrieve({ page_id });
    return { content: [{ type: "text", text: JSON.stringify(page, null, 2) }], structuredContent: page };
  } catch (err) { notionError(err, "notion_get_page"); }
});

server.registerTool("notion_get_page_content", {
  description: "Get the body content of a Notion page as an array of blocks (paragraphs, headings, lists, etc.).",
  inputSchema: {
    page_id: z.string().describe("Notion page ID from the URL"),
    max_blocks: z.number().min(1).max(500).default(100).describe("Max blocks to return (1-500)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ page_id, max_blocks }) => {
  try {
    const blocks = await paginate(
      (cursor) => notion.blocks.children.list({ block_id: page_id, start_cursor: cursor, page_size: 100 }) as any,
      max_blocks
    );
    const result = { page_id, block_count: blocks.length, blocks };
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], structuredContent: result };
  } catch (err) { notionError(err, "notion_get_page_content"); }
});

server.registerTool("notion_create_page", {
  description: "Create a new Notion page inside a database or as a child of an existing page. Returns the new page ID and URL.",
  inputSchema: {
    parent_id: z.string().describe("Database ID (to create a database entry) or page ID (to create a subpage)"),
    parent_type: z.enum(["database", "page"]).describe("Whether parent_id is a database or page"),
    title: z.string().describe("Page title text"),
    properties: z.string().optional().describe("JSON object of additional database properties, e.g. {\"Status\":{\"select\":{\"name\":\"In Progress\"}}}"),
  },
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false },
}, async ({ parent_id, parent_type, title, properties }) => {
  try {
    const extraProps = properties ? JSON.parse(properties) : {};
    const page = await notion.pages.create({
      parent: parent_type === "database" ? { database_id: parent_id } : { page_id: parent_id },
      properties: {
        title: { title: [{ text: { content: title } }] },
        ...extraProps,
      },
    });
    const result = { id: (page as any).id, url: (page as any).url, title };
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], structuredContent: result };
  } catch (err) { notionError(err, "notion_create_page"); }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Phase 3: Build & Test

```bash
npm run build

NOTION_API_KEY=secret_your_token npx @modelcontextprotocol/inspector node dist/index.js
```

Inspector checklist:
- [ ] `notion_list_databases` returns your shared databases
- [ ] `notion_query_database` with a real database ID returns pages
- [ ] `notion_create_page` creates a page visible in Notion
- [ ] Invalid database ID returns helpful error mentioning "shared with your integration"

## Phase 4: Sample Evaluations

```xml
<evaluation>
  <qa_pair>
    <question>Using the notion_list_databases tool, what is the ID of the database with "Tasks" in its title?</question>
    <answer>abc123def456...</answer>
  </qa_pair>
  <qa_pair>
    <question>Query the Tasks database for pages with Status = "Done". How many results are returned?</question>
    <answer>7</answer>
  </qa_pair>
</evaluation>
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "notion": {
      "command": "node",
      "args": ["/path/to/notion-mcp/dist/index.js"],
      "env": { "NOTION_API_KEY": "secret_your_token_here" }
    }
  }
}
```
