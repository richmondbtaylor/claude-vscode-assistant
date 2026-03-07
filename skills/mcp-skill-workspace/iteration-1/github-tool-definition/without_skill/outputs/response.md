# Writing Great MCP Tool Definitions for GitHub API: List Pull Requests

## The Complete Tool Definition

```typescript
{
  name: "list_pull_requests",
  description: `List pull requests for a GitHub repository.

Returns an array of pull request objects matching the specified filters. Use this tool when you need to:
- Find open, closed, or merged pull requests in a repository
- Search for PRs by author, branch, or label
- Get a summary of recent PR activity
- Locate a specific PR by its head branch or base branch

Results are paginated (default 30 per page, max 100). Use the 'page' parameter to retrieve subsequent pages.

Note: Requires at least read access to the repository. For private repositories, the authenticated user must have explicit access.`,

  annotations: {
    title: "List Pull Requests",
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: true
  },

  inputSchema: {
    type: "object",
    properties: {
      owner: {
        type: "string",
        description: "The GitHub username or organization name that owns the repository."
      },
      repo: {
        type: "string",
        description: "The repository name (without the owner prefix)."
      },
      state: {
        type: "string",
        enum: ["open", "closed", "all"],
        default: "open",
        description: "Filter pull requests by state."
      },
      per_page: {
        type: "integer",
        minimum: 1,
        maximum: 100,
        default: 30,
        description: "Number of results per page (max 100)."
      },
      page: {
        type: "integer",
        minimum: 1,
        default: 1,
        description: "Page number (1-indexed)."
      }
    },
    required: ["owner", "repo"]
  }
}
```

## Annotations Explained

| Annotation | Value | Reason |
|---|---|---|
| `readOnlyHint` | `true` | Only performs GET requests — no side effects |
| `destructiveHint` | `false` | Cannot delete or modify anything |
| `idempotentHint` | `true` | Same parameters always yield the same result |
| `openWorldHint` | `true` | Accesses live external data from GitHub |

## Key Principles

1. **Descriptions explain when AND what** — not just what the parameter is named
2. **Annotate read-only tools** so clients skip unnecessary confirmation dialogs
3. **Document non-obvious formats** like `user:branch` for the `head` parameter
4. **Put pagination info at the top level** so models see it before scanning parameters
5. **Explain enum values individually** so models can match user intent to the right value
6. **Use `default` in schema** so models know what happens when parameters are omitted

*(Note: agent hit permission denial — response captured from task output. Uses raw JSON schema, not Zod/server.registerTool pattern.)*
