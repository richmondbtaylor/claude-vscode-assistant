---
name: mcp-skill
description: "Guides you through building a complete MCP (Model Context Protocol) server from scratch — research, design, implementation, testing, and evaluation. Use this skill whenever you want to build an MCP server, create MCP tools, develop an MCP integration, expose an API via MCP, or let Claude interact with any external service or database through tools. Trigger on: 'build an MCP server', 'create MCP tools', 'make an MCP integration', 'I want Claude to be able to use X API', 'expose X to Claude via MCP', 'add MCP support for', 'write an MCP server for', 'create tools for Claude to use', 'MCP server development', 'register tools with MCP'. Even if the user just says 'help me with MCP' or 'I want Claude to interact with my database', use this skill."
---

# MCP Server Development

Build a production-quality MCP server that lets LLMs interact with external services through well-designed tools. Quality = how well an LLM can accomplish real-world tasks using your tools.

## Before You Start

Load these docs now using WebFetch (they're short and essential):

1. **MCP Protocol overview** — fetch `https://modelcontextprotocol.io/introduction.md`
2. **TypeScript SDK README** — fetch `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`

If the user wants Python instead, fetch `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md` too.

Also identify the target API: look up its documentation so you understand endpoints, auth, and data models before designing tools.

---

## Phase 1: Research & Planning

### What kind of tools?

Two types — and you usually want both:

- **API coverage tools**: Thin wrappers around individual endpoints. Gives agents flexibility to compose operations. Priority for most servers.
- **Workflow tools**: Higher-level operations that combine multiple steps. Add these for common tasks that agents do repeatedly.

When uncertain, lead with comprehensive API coverage. Agents with code execution can compose basic tools; they can't fill in missing endpoints.

### Tool naming

Use consistent action prefixes: `list_`, `get_`, `create_`, `update_`, `delete_`, `search_`. Include a service prefix when the server covers one domain (e.g., `github_list_repos`, `github_create_issue`). This helps agents scan and find the right tool quickly.

### Plan your tool set

Before writing code, list the tools you'll build:
- What are the top 5-10 operations a developer would need?
- Which require read-only vs. write access?
- What's the minimum input to make each call? What's the useful output?

---

## Phase 2: Implementation

### Recommended stack
- **Language**: TypeScript (preferred — strong SDK, static types help catch bugs)
- **Transport**: `stdio` for local tools, streamable HTTP for remote servers
- **Schema**: Zod for input validation

### Project setup (TypeScript)

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node ts-node
```

`tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "strict": true
  },
  "include": ["src/**/*"]
}
```

`package.json` scripts:
```json
{
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts"
  }
}
```

### Server skeleton (TypeScript)

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "my-service-mcp",
  version: "1.0.0",
});

// Register tools here (see below)

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Each tool should have

1. **Input schema** — Zod with `.describe()` on every field and reasonable constraints:
   ```typescript
   server.registerTool(
     "list_repos",
     {
       description: "List GitHub repositories for a user or org. Returns name, description, stars, and last push date.",
       inputSchema: {
         owner: z.string().describe("GitHub username or organization name"),
         type: z.enum(["all", "public", "private"]).default("public").describe("Filter by repo visibility"),
         per_page: z.number().min(1).max(100).default(30).describe("Results per page (max 100)"),
       },
       annotations: { readOnlyHint: true },
     },
     async ({ owner, type, per_page }) => {
       // implementation
     }
   );
   ```

2. **Output** — return both human-readable text and structured data:
   ```typescript
   return {
     content: [{ type: "text", text: JSON.stringify(repos, null, 2) }],
     structuredContent: { repos },
   };
   ```

3. **Annotations** — always include:
   - `readOnlyHint: true` — for GET/read operations
   - `destructiveHint: true` — for delete/overwrite operations
   - `idempotentHint: true` — for PUT/upsert operations

4. **Error messages** — be specific and actionable:
   ```typescript
   // Bad:  "API error"
   // Good: `GitHub API 404: repository '${owner}/${repo}' not found. Check spelling and that you have access.`
   ```

### Core infrastructure to build first

Before individual tools, create shared utilities:

- **Auth helper**: Read credentials from env vars (`process.env.GITHUB_TOKEN`), validate on startup, attach to all requests
- **HTTP client**: A thin wrapper that handles base URL, auth headers, and rate limits
- **Error handler**: Map API errors to actionable messages
- **Paginator**: A reusable function to fetch paginated results with a `max_results` cap

---

## Phase 3: Review & Test

### Code quality check (before testing)

- No duplicated API call logic — extract to shared client
- Every `async` function has try/catch with meaningful error messages
- Every tool input has `.describe()` annotations
- No any types — use proper TypeScript interfaces for API responses
- Tool descriptions tell the agent *what it returns*, not just what it does

### Build and test

```bash
npm run build
```

Test interactively with MCP Inspector:
```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

In the Inspector:
1. Verify each tool appears with correct descriptions
2. Call each tool with valid inputs — confirm correct output
3. Call each tool with invalid inputs — confirm helpful error messages
4. Test pagination with `per_page` limits

### Python alternative

If using Python with FastMCP:
```bash
pip install fastmcp httpx
python -m py_compile server.py  # syntax check
fastmcp dev server.py            # runs with MCP Inspector
```

---

## Phase 4: Evaluations

After the server is working, create evaluations that test whether an LLM can actually use it to answer realistic questions.

### The process

1. **Inspect your tools** — list all registered tools and understand what they return
2. **Explore data** — use READ-ONLY tool calls to look at real content: what repos exist, what issues are open, what data is there
3. **Write 10 questions** — complex, multi-step, realistic (see requirements below)
4. **Verify each answer** — run the tools yourself to confirm the exact answer

### Question requirements

Every question must be:
- **Independent** — doesn't depend on other questions
- **Read-only** — answerable without creating/deleting anything
- **Complex** — requires calling 2+ tools or exploring multiple endpoints
- **Realistic** — something a real user or developer would actually want to know
- **Verifiable** — has one specific, unambiguous answer (a number, a name, a date, a quoted string)
- **Stable** — answer won't change as data changes (use historical data, fixed IDs, etc.)

Good example:
> "In the anthropics/anthropic-sdk-python repository, what is the name of the GitHub Actions workflow that runs on pull requests targeting the main branch, and how many jobs does it define?"

Bad example:
> "How many open issues are there?" (changes over time, not stable)

### Output format

```xml
<evaluation>
  <qa_pair>
    <question>Find the GitHub issue in the modelcontextprotocol/typescript-sdk repo that discusses rate limiting. What is the issue number and who opened it?</question>
    <answer>Issue #42, opened by user @octocat</answer>
  </qa_pair>
  <!-- 9 more qa_pairs... -->
</evaluation>
```

Save as `evaluations.xml` in your project root.

---

## Quick Reference

| Phase | Key output |
|-------|-----------|
| 1. Research | Tool list with names, descriptions, auth plan |
| 2. Implementation | Working TypeScript/Python MCP server |
| 3. Testing | `npm run build` passes + Inspector verified |
| 4. Evaluations | `evaluations.xml` with 10 Q&A pairs |

**Useful links** (fetch as needed):
- MCP spec pages: `https://modelcontextprotocol.io/<page>.md` (see sitemap at `/sitemap.xml`)
- TS SDK: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- Python SDK: `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
