---
name: codecraft
description: "Generates a complete, enterprise-grade React documentation system — including coding standards, testing guidelines, security protocols, ESLint/Prettier configurations, and React-specific patterns — organized into a Claude/rules/ hierarchy. Use this skill whenever a user wants to: set up coding standards or a style guide for a React project, generate documentation for their dev team, create onboarding docs, establish testing conventions, document security practices for a frontend app, generate ESLint or Prettier config, create a project README system, set up pre-commit hooks, or systematize any aspect of how their React team writes code. Trigger on: 'set up coding standards', 'create React docs', 'generate style guide', 'set up linting', 'create development guidelines', 'documentation system', 'coding conventions', 'project standards', 'React best practices', 'team coding guide', 'code review checklist', 'set up husky', 'ESLint config', 'testing standards'. Even if the user just says 'I need coding standards' or 'help me document my React project' or 'set up code quality tools', use this skill."
---

# CodeCraft — React Documentation System Generator

Generate a complete, immediately usable documentation system for a React development team. The output is a `Claude/rules/` directory hierarchy with six interconnected files covering every major concern: code style, testing, security, React patterns, component styling, and local tooling config.

## Reference Files

This skill ships with complete, production-ready templates. Read them as needed:

| File | When to read |
|------|-------------|
| `references/styles-guide.md` | Generating `Claude/rules/styles.md` |
| `references/testing-guide.md` | Generating `Claude/rules/testing.md` |
| `references/security-guide.md` | Generating `Claude/rules/security.md` |
| `references/react-guide.md` | Generating `Claude/rules/frontend/React.md` |
| `references/frontend-styles.md` | Generating `Claude/rules/frontend/styles.md` |
| `references/mcp-config.json` | Generating `Claude/rules/.mcp.json` |

---

## Phase 1: Gather Project Context

Before generating anything, ask the user 3–5 questions to understand what to customize. Keep it conversational — you don't need answers to every edge case, just enough to tailor the output:

1. **Project name and brief description** — what does the app do?
2. **TypeScript or JavaScript?** — this changes naming conventions and examples throughout
3. **Styling approach** — CSS Modules, styled-components, Tailwind, or a mix?
4. **State management** — local state only, Context API, Redux, Zustand, or other?
5. **Any existing tooling** — do they already have ESLint, Prettier, Husky, or CI/CD set up?

If the user wants to skip questions and just generate defaults, proceed with: TypeScript, CSS Modules, Context API for global state, and no existing tooling assumed.

---

## Phase 2: Output Structure

Generate exactly these files in this structure:

```
Claude/
└── rules/
    ├── styles.md           ← JS/TS code style standards
    ├── testing.md          ← Jest + React Testing Library
    ├── security.md         ← Frontend security protocols
    ├── frontend/
    │   ├── React.md        ← Hooks, lifecycle, performance
    │   └── styles.md       ← Component styling conventions
    └── .mcp.json           ← Local dev server + tool config
```

Every markdown file must follow this standard structure (see reference files for full content):

1. Introduction (scope + audience)
2. Table of Contents (linked)
3. Core Guidelines (rules + rationale)
4. Common Patterns (runnable examples)
5. Anti-Patterns (❌ Avoid / ✅ Prefer format)
6. Tooling & Automation (configs + setup)
7. Real-World Examples (before/after)
8. Customization (how to adapt for project needs)

---

## Phase 3: Generate Each File

Work through the files in this order. Read the corresponding reference file before writing each one, then customize it for the project context gathered in Phase 1.

### File 1: `Claude/rules/styles.md`

Read `references/styles-guide.md`. Customize:
- Replace TypeScript/JavaScript examples based on user's choice
- Update import ordering if they have specific libraries
- Adjust file organization to match their existing structure (if shared)
- Include their specific ESLint extends (e.g., if they use `plugin:react/recommended`)

### File 2: `Claude/rules/testing.md`

Read `references/testing-guide.md`. Customize:
- Match test utilities to their project (e.g., custom render wrappers if they use Redux or a specific provider setup)
- If they already have a test directory structure, document it; otherwise use the recommended structure
- Coverage thresholds: default to 80% statements/branches/functions

### File 3: `Claude/rules/security.md`

Read `references/security-guide.md`. Customize:
- If they use JWT stored in localStorage, document the trade-offs and recommended migration path
- If they use httpOnly cookies, document the CSRF protection requirements
- Tailor API call examples to their actual base URL pattern if known

### File 4: `Claude/rules/frontend/React.md`

Read `references/react-guide.md`. Customize:
- State management section: emphasize whichever approach they use
- If TypeScript, show typed interfaces for all component props; if JS, show PropTypes
- Performance section: tailor memoization examples to their component patterns

### File 5: `Claude/rules/frontend/styles.md`

Read `references/frontend-styles.md`. Customize:
- Lead with their primary styling approach (CSS Modules, styled-components, Tailwind)
- Include their theme configuration structure if they have one
- Document their breakpoints if known, or use standard mobile/tablet/desktop defaults

### File 6: `Claude/rules/.mcp.json`

Read `references/mcp-config.json`. Customize:
- Update `projectName` and `rootDir`
- Set ports based on their package.json `start` script if known
- Add any CI/testing environment variables they mentioned

---

## Phase 4: Enforcement Configurations

After the main docs, generate these ready-to-use config files in the project root:

### `.eslintrc.json`
Complete configuration matching the style guidelines. Include commented explanations for non-obvious rules. Extend from their existing config if they mentioned one.

### `.prettierrc`
Matching formatting rules. Print width 100, single quotes, trailing commas, semicolons.

### `package.json` additions
Add the `lint-staged`, `husky`, and `scripts` sections. Show how to merge with their existing package.json rather than replacing it.

### `.husky/pre-commit`
Run ESLint, Prettier check, and `npm test -- --watchAll=false` before commits.

### `.github/workflows/ci.yml`
GitHub Actions workflow: lint, format check, type check (if TypeScript), test.

### `.vscode/settings.json`
Format on save, ESLint auto-fix on save, Prettier as default formatter.

---

## Phase 5: Cross-Reference and Index

After all files are generated, create a brief summary for the user:

```
✅ Generated Claude/rules/ documentation system

Files created:
  Claude/rules/styles.md          — Code style & ESLint standards
  Claude/rules/testing.md         — Jest + RTL testing framework
  Claude/rules/security.md        — XSS, auth, API security protocols
  Claude/rules/frontend/React.md  — Hooks, performance, state patterns
  Claude/rules/frontend/styles.md — Component styling conventions
  Claude/rules/.mcp.json          — Local dev server configuration

Enforcement tools generated:
  .eslintrc.json     — ESLint configuration
  .prettierrc        — Prettier formatting rules
  .husky/pre-commit  — Pre-commit hooks
  .github/workflows/ci.yml — CI/CD pipeline
  .vscode/settings.json    — Editor integration

Next steps:
  1. Run: npm install --save-dev eslint prettier husky lint-staged
  2. Run: npx husky install
  3. Review Claude/rules/styles.md and adjust ESLint rules to your team's preferences
  4. Share the Claude/rules/ folder with your team
```

---

## Code Example Standards

All code examples in generated files must:

- Use triple-backtick blocks with language identifiers (`javascript`, `typescript`, `jsx`, `tsx`, `json`, `bash`)
- Show complete implementations: imports, component, types, export — no fragments
- Use `❌ Avoid` and `✅ Prefer` labels for anti-pattern comparisons
- Include inline comments explaining non-obvious decisions
- Use ASCII tree notation for file structure diagrams

---

## Maintenance Protocol

At the end of each generated markdown file, include this section:

```markdown
## Version and Maintenance

- **Version**: 1.0.0
- **Last Updated**: [current date]
- **Review Cycle**: Quarterly
- **Owner**: [team or person responsible]

### Changelog
| Version | Date | Change | Reason |
|---------|------|--------|--------|

### Update Process
1. Propose changes in a PR with rationale
2. Peer review required before merging
3. Test all code examples in a real dev environment
4. Update version and changelog entry
5. Announce breaking changes to team with migration guidance
```
