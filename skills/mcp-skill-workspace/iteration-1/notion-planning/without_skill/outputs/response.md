# Building an MCP Server for the Notion API

## Overview

The Model Context Protocol (MCP) is an open standard that allows AI assistants like Claude to connect to external tools and data sources via a standardized server interface. Building an MCP server for Notion will let Claude list databases, query pages, and create new pages directly during conversations.

---

## Prerequisites

Before you start, you need:

1. A Notion account with an integration token (internal integration)
2. Node.js 18+ (or Python 3.10+ if you prefer Python)
3. The Notion API credentials - create an integration at https://www.notion.so/my-integrations
4. MCP SDK - the official TypeScript or Python SDK from Anthropic

---

## Step 1: Set Up Your Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Give it a name (e.g., "Claude MCP Integration")
4. Select the workspace
5. Copy the **Internal Integration Token** (starts with `secret_...`)
6. Share the specific Notion databases/pages you want to access with the integration (open the page in Notion, click "..." > "Add connections" > select your integration)

---

## Step 2: Initialize the MCP Server Project

```bash
mkdir notion-mcp-server
cd notion-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk @notionhq/client zod
npm install -D typescript @types/node ts-node
npx tsc --init
```

---

## Step 3: Three Core Tools to Build

### Tool 1: `notion_list_databases` - Lists all accessible databases
### Tool 2: `notion_query_database` - Queries pages from a database with optional filters
### Tool 3: `notion_create_page` - Creates a new page in a database or as a subpage

---

## Step 4: Configure in Claude

Add to `~/.claude/settings.json` under `"mcpServers"`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "node",
      "args": ["/path/to/notion-mcp-server/dist/index.js"],
      "env": { "NOTION_API_KEY": "secret_your_token_here" }
    }
  }
}
```

*(Note: agent hit permission denial — response is partial, full code samples not captured)*
