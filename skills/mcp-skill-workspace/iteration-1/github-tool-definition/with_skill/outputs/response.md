# Writing a Great MCP Tool Definition: `github_list_pull_requests`

## The Complete Tool Definition

```typescript
server.registerTool(
  "github_list_pull_requests",
  {
    title: "List Pull Requests",
    description:
      "List pull requests for a GitHub repository. Returns PR number, title, state, " +
      "author login, labels, assignees, milestone, head/base branch names, draft status, " +
      "and timestamps (created_at, updated_at, merged_at). Supports filtering by state, " +
      "head branch, base branch, and sort order. Results are paginated; use `page` and " +
      "`per_page` to walk through large result sets. Requires a token with `repo` scope " +
      "for private repositories; public repositories work without authentication.",
    inputSchema: {
      owner: z.string().describe(
        "GitHub username or organization name that owns the repository (e.g. 'octocat' or 'microsoft')"
      ),
      repo: z.string().describe(
        "Repository name without the owner prefix (e.g. 'hello-world', not 'octocat/hello-world')"
      ),
      state: z.enum(["open", "closed", "all"]).default("open").describe(
        "'open' = currently open, 'closed' = merged or rejected, 'all' = every PR regardless of state. Defaults to 'open'."
      ),
      head: z.string().optional().describe(
        "Filter by head branch. Use 'user:branch-name' format to filter across forks (e.g. 'octocat:feature-login'), or just 'branch-name' within the same repo."
      ),
      base: z.string().optional().describe(
        "Filter by base (target) branch name (e.g. 'main', 'develop'). Only returns PRs targeting this branch."
      ),
      sort: z.enum(["created", "updated", "popularity", "long-running"]).default("created").describe(
        "'created' = creation time, 'updated' = last update, 'popularity' = comment count, 'long-running' = oldest open PRs first."
      ),
      direction: z.enum(["asc", "desc"]).default("desc").describe(
        "'desc' = newest/highest first (default), 'asc' = oldest/lowest first."
      ),
      per_page: z.number().int().min(1).max(100).default(30).describe(
        "Results per page (1-100). Use 100 to minimize API calls. Defaults to 30."
      ),
      page: z.number().int().min(1).default(1).describe(
        "Page number (1-indexed). If the response returns fewer items than per_page, you are on the last page."
      ),
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true,
    },
  },
  async ({ owner, repo, state, head, base, sort, direction, per_page, page }) => {
    const params = new URLSearchParams({ state, sort, direction, per_page: String(per_page), page: String(page) });
    if (head) params.set("head", head);
    if (base) params.set("base", base);

    const response = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/pulls?${params}`,
      {
        headers: {
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          ...(process.env.GITHUB_TOKEN ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } : {}),
        },
      }
    );

    if (!response.ok) {
      const body = await response.text();
      throw new Error(
        `GitHub API ${response.status} for ${owner}/${repo}: ${body}. ` +
        (response.status === 404 ? "Check that the repository exists and you have access." :
         response.status === 401 ? "Set GITHUB_TOKEN env var with a valid personal access token." :
         response.status === 403 ? "Rate limit exceeded or insufficient token scope." : "")
      );
    }

    const hasNextPage = (response.headers.get("link") ?? "").includes('rel="next"');
    const pulls = await response.json();

    const items = pulls.map((pr) => ({
      number: pr.number,
      title: pr.title,
      state: pr.state,
      draft: pr.draft,
      author: pr.user?.login ?? null,
      labels: pr.labels.map((l) => l.name),
      assignees: pr.assignees.map((a) => a.login),
      milestone: pr.milestone?.title ?? null,
      head_branch: pr.head.ref,
      base_branch: pr.base.ref,
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      merged_at: pr.merged_at ?? null,
      html_url: pr.html_url,
    }));

    const summary = {
      repository: `${owner}/${repo}`,
      filter: { state, head: head ?? null, base: base ?? null },
      pagination: { page, per_page, has_next_page: hasNextPage },
      count: items.length,
      pull_requests: items,
    };

    return {
      content: [{ type: "text", text: JSON.stringify(summary, null, 2) }],
      structuredContent: summary,
    };
  }
);
```

## Key Principles Explained

**Tool Name** (`github_list_pull_requests`): Uses `{service}_{action}_{resource}` pattern.

**Description**: Leads with what is returned (field names), mentions filters and pagination, states auth requirements. The LLM selects your tool based almost entirely on the description.

**Every input `.describe()`**:
- Format hints with examples prevent mistakes (e.g. `repo` says "not 'octocat/hello-world'")
- Enum values get individual explanations
- Pagination fields explain the stopping condition

**Annotations**:

| Annotation | Value | Why |
|---|---|---|
| `readOnlyHint: true` | true | GET operation, never modifies data, safe to retry |
| `destructiveHint: false` | false | Explicitly false — do not leave undefined |
| `idempotentHint: true` | true | Same args = same result, safe to retry on timeout |
| `openWorldHint: true` | true | Calls external API (GitHub), results reflect live state |

**Output shaping**: Returns only 14 fields from the raw 80-field GitHub response. Returns both `content` (text) and `structuredContent` (typed object for modern clients). Includes `has_next_page` parsed from the `Link` header.

**Error messages**: Status code + affected resource + specific fix. "GitHub API 404 for octocat/hello-world: Check that the repository exists and you have access." beats "Not found" every time.
