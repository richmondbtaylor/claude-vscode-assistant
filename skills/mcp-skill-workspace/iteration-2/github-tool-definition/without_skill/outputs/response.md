# Building a Great MCP Tool Definition for List Pull Requests (Haiku Baseline)

## Core Principles

1. **Clarity**: Describe what the tool does in simple, direct language
2. **Completeness**: Include all required and optional parameters
3. **Specificity**: Be precise about data formats, ranges, and expected values
4. **Examples**: Provide realistic examples when possible
5. **Constraints**: Document any limitations or special requirements

## Example Tool Definition

```typescript
{
  name: "github_list_pull_requests",
  description: "List pull requests for a GitHub repository with optional filtering and sorting. Returns paginated results of pull requests matching the specified criteria.",
  inputSchema: {
    type: "object" as const,
    properties: {
      owner: {
        type: "string",
        description: "The repository owner's login username or organization name.",
        examples: ["octocat", "github"]
      },
      repo: {
        type: "string",
        description: "The repository name.",
        examples: ["Hello-World", "cli"]
      },
      state: {
        type: "string",
        enum: ["open", "closed", "all"],
        description: "Filter pull requests by state. Defaults to 'open'.",
        default: "open"
      },
      sort: {
        type: "string",
        enum: ["created", "updated", "popularity", "long-running"],
        description: "Sort order. Defaults to 'created'.",
        default: "created"
      },
      direction: {
        type: "string",
        enum: ["asc", "desc"],
        description: "Sort direction. Defaults to 'desc'.",
        default: "desc"
      },
      per_page: {
        type: "integer",
        description: "Number of results per page. Must be between 1 and 100.",
        minimum: 1,
        maximum: 100,
        default: 30
      },
      page: {
        type: "integer",
        description: "Page number for pagination. Starts at 1.",
        minimum: 1,
        default: 1
      }
    },
    required: ["owner", "repo"],
    additionalProperties: false
  }
}
```

## Annotations

```typescript
annotations: {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true
}
```

## Best Practices

1. Use clear action verbs (List, Get, Create)
2. Document constraints with min/max
3. Use enum for fixed value sets
4. Include default values
5. Set `additionalProperties: false`
6. Always include pagination parameters with bounds

*(Note: Haiku baseline — uses raw JSON Schema, not Zod. No server.registerTool pattern. No handler/structuredContent shown.)*
