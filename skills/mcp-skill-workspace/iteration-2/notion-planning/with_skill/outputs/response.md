# Building an MCP Server for the Notion API (Haiku + Skill)

## Phase 1: Research & Planning

**Tool Strategy:** 10 total tools (6 read-only + 3 write + 1 workflow)

### Read-Only Tools
1. `notion_list_databases` — Discover accessible databases
2. `notion_get_database_schema` — Learn database structure
3. `notion_query_database` — Search/filter pages with sorting
4. `notion_get_page` — Retrieve single page properties
5. `notion_get_page_content` — Read block content
6. `notion_search` — Global keyword search

### Write Tools
7. `notion_create_page` — Create new database entries
8. `notion_update_page_properties` — Modify existing pages
9. `notion_append_block_children` — Add content blocks

### Workflow Tool
10. `notion_create_database_page` — High-level simplified creation

**Auth:** Bearer token via `NOTION_API_KEY` env var

## Phase 2: Implementation

**Stack:** TypeScript + MCP SDK + Zod validation

**Project structure:**
```
src/
  auth.ts
  client.ts
  tools/
  types.ts
```

Each tool uses `server.registerTool` with Zod input schemas, `.describe()` on all fields, proper error handling, and tool annotations (`readOnlyHint: true` on read tools).

## Phase 3: Testing

MCP Inspector setup and testing checklist:
```bash
NOTION_API_KEY=secret_... npx @modelcontextprotocol/inspector node dist/index.js
```

Testing checklist:
- [ ] notion_list_databases returns shared databases
- [ ] notion_query_database with a real database ID returns pages
- [ ] notion_create_page creates a visible page in Notion
- [ ] Invalid IDs return helpful errors mentioning "share with integration"

## Phase 4: Evaluations

10 complex, multi-step test questions in XML format:
```xml
<evaluation>
  <qa_pair>
    <question>List all accessible Notion databases. How many are there and what are their titles?</question>
    <answer>...</answer>
  </qa_pair>
</evaluation>
```

*(Note: Haiku with skill — agent produced summary, could not write files due to permission denial)*
