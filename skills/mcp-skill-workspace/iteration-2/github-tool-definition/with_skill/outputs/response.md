# Building a Great Tool Definition: GitHub List Pull Requests (Haiku + Skill)

## The Complete Tool Definition

```typescript
server.registerTool(
  "github_list_pull_requests",
  {
    description: "List pull requests in a GitHub repository. Returns PR number, title, author, status (open/closed/draft), creation date, and last update date. Use this to discover open PRs, find work in progress, or check PR history.",
    inputSchema: {
      owner: z.string().describe("GitHub repository owner (username or organization name)"),
      repo: z.string().describe("GitHub repository name (the part after the owner in the URL)"),
      state: z.enum(["open", "closed", "all"]).default("open")
        .describe("Filter by PR state. 'open' = open PRs only, 'closed' = closed/merged only, 'all' = both"),
      sort: z.enum(["created", "updated", "popularity", "long-running"]).default("created")
        .describe("Sort results: 'created' (newest first), 'updated' (recently modified), 'popularity' (most comments), 'long-running' (oldest open)"),
      direction: z.enum(["asc", "desc"]).default("desc")
        .describe("'desc' = descending order (default), 'asc' = ascending order"),
      per_page: z.number().min(1).max(100).default(30)
        .describe("Number of results per page (max 100). Set lower for faster responses"),
      labels: z.string().optional()
        .describe("Comma-separated list of labels to filter by (e.g., 'bug,enhancement'). Only returns PRs with ALL specified labels"),
      assignee: z.string().optional()
        .describe("GitHub username. Only returns PRs assigned to this user. Use 'none' for unassigned"),
      creator: z.string().optional()
        .describe("GitHub username. Only returns PRs opened by this user"),
      max_results: z.number().min(1).default(100)
        .describe("Stop after fetching this many results (will paginate if needed)"),
    },
    annotations: {
      readOnlyHint: true,
    },
  },
  async ({ owner, repo, state, sort, direction, per_page, labels, assignee, creator, max_results }) => {
    const params = new URLSearchParams({ state, sort, direction, per_page: String(per_page) });
    if (labels) params.append("labels", labels);
    if (assignee) params.append("assignee", assignee);
    if (creator) params.append("creator", creator);

    const allPRs = [];
    let page = 1;

    while (allPRs.length < max_results) {
      params.set("page", String(page));
      const response = await fetch(
        `https://api.github.com/repos/${owner}/${repo}/pulls?${params}`,
        { headers: { Authorization: `token ${process.env.GITHUB_TOKEN}`, Accept: "application/vnd.github.v3+json" } }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Repository '${owner}/${repo}' not found. Check the owner and repo names are correct.`);
        }
        throw new Error(`GitHub API error ${response.status}: ${response.statusText}`);
      }

      const prs = await response.json();
      if (!prs.length) break;

      allPRs.push(...prs.map((pr) => ({
        number: pr.number,
        title: pr.title,
        author: pr.user.login,
        state: pr.state,
        draft: pr.draft,
        created_at: pr.created_at,
        updated_at: pr.updated_at,
        url: pr.html_url,
        labels: pr.labels.map((l) => l.name),
        assignees: pr.assignees.map((a) => a.login),
        comment_count: pr.comments,
      })));
      page++;
    }

    const results = allPRs.slice(0, max_results);
    return {
      content: [{ type: "text", text: `Found ${results.length} pull requests in ${owner}/${repo}\n\n${JSON.stringify(results, null, 2)}` }],
      structuredContent: { repository: `${owner}/${repo}`, total_returned: results.length, pull_requests: results },
    };
  }
);
```

## Key Principles Applied

**Description names return fields**: PR number, title, author, status, dates — agent knows exactly what it's getting.

**Zod with `.describe()` on every field**: Each explains the "why" not just the "what" (e.g. `'none' for unassigned`).

**`readOnlyHint: true`**: Signals safe to call multiple times without side effects.

**Pagination with `max_results`**: Lets agent control total results and avoid rate limits.

**`content` + `structuredContent`**: Text for compatibility, structured object for reasoning.

**Actionable errors**: 404 says "Check the owner and repo names" not just "Not found".
