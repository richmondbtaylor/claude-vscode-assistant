# Code Style Standards
> Template for `Claude/rules/styles.md`

## Introduction

This document defines code style standards for the React application. It applies to every JavaScript/TypeScript file in the codebase and is enforced automatically via ESLint, Prettier, and pre-commit hooks. All contributors — including contractors and AI coding assistants — are expected to follow these standards before submitting code for review.

**Audience:** All developers writing or reviewing code in this repository.

---

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [File Organization](#file-organization)
3. [Import & Export Structure](#import--export-structure)
4. [Component Architecture](#component-architecture)
5. [TypeScript Conventions](#typescript-conventions)
6. [Common Patterns](#common-patterns)
7. [Anti-Patterns](#anti-patterns)
8. [Tooling & Automation](#tooling--automation)
9. [Examples](#examples)
10. [Customization](#customization)

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| React components | PascalCase | `UserProfile`, `NavigationMenu` |
| Functions & variables | camelCase | `fetchUserData`, `isLoading` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| TypeScript interfaces | PascalCase, no `I` prefix | `UserProfile`, `ApiResponse` |
| TypeScript types | PascalCase | `ButtonVariant`, `ThemeMode` |
| CSS classes | kebab-case | `user-profile`, `nav-menu__item` |
| Files: components | PascalCase | `UserProfile.tsx` |
| Files: hooks | camelCase, `use` prefix | `useUserData.ts` |
| Files: utilities | camelCase | `formatDate.ts` |
| Files: tests | same as source + `.test` | `UserProfile.test.tsx` |
| Files: types | PascalCase or camelCase | `types.ts`, `UserProfile.types.ts` |

**Why these conventions matter:** Consistent naming removes cognitive load — a developer encountering `useUserData` immediately knows it's a hook, just as `UserProfile` signals a component. This becomes especially valuable in large codebases where you're reading unfamiliar code.

---

## File Organization

Use a feature-based structure. Group by domain, not by type.

```
src/
├── components/           ← Shared, reusable UI components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   ├── Button.module.css
│   │   └── index.ts      ← Public API: export { Button } from './Button'
│   └── Modal/
│       ├── Modal.tsx
│       ├── Modal.test.tsx
│       └── index.ts
├── features/             ← Feature-specific modules
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── LoginForm.test.tsx
│   │   ├── hooks/
│   │   │   └── useAuth.ts
│   │   ├── api/
│   │   │   └── authApi.ts
│   │   └── index.ts
│   └── dashboard/
├── hooks/                ← Shared custom hooks
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
├── utils/                ← Pure utility functions
│   ├── formatDate.ts
│   └── validators.ts
├── types/                ← Global TypeScript types
│   └── api.types.ts
├── constants/            ← App-wide constants
│   └── config.ts
└── styles/               ← Global styles
    ├── globals.css
    └── variables.css
```

**Rule:** A feature folder owns everything related to that feature. Shared utilities live at the top level. Never put shared utilities inside a feature folder.

---

## Import & Export Structure

Imports must be ordered in exactly four groups, separated by blank lines:

1. External libraries (`react`, `axios`, third-party packages)
2. Internal modules (path aliases like `@/components`, `@/hooks`)
3. Relative imports (`../`, `./`)
4. Style imports (`.css`, `.module.css`)

```typescript
// ✅ Correct import order
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';

import { formatDate } from '../utils/formatDate';
import { UserCard } from './UserCard';

import styles from './UserProfile.module.css';
```

**Named exports preferred over default exports** for non-component files. Components use default exports for dynamic import compatibility.

```typescript
// ✅ Utilities: named exports
export const formatDate = (date: Date): string => { ... };
export const isValidEmail = (email: string): boolean => { ... };

// ✅ Components: default export + named re-export from index.ts
export default function UserProfile({ userId }: Props) { ... }
// index.ts: export { default as UserProfile } from './UserProfile';
```

---

## Component Architecture

Every React component file follows this structure:

```typescript
// 1. Imports (ordered per above)
import React, { useState, useCallback } from 'react';
import type { FC } from 'react';

import { Button } from '@/components/Button';
import { useUserData } from '@/hooks/useUserData';

import styles from './UserProfile.module.css';

// 2. Types/interfaces (co-located with component)
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
  className?: string;
}

// 3. Constants used only by this component
const MAX_BIO_LENGTH = 250;

// 4. Component definition
const UserProfile: FC<UserProfileProps> = ({ userId, onUpdate, className }) => {
  // 4a. Hooks (useState, useEffect, custom hooks) at the top
  const [isEditing, setIsEditing] = useState(false);
  const { user, isLoading, error } = useUserData(userId);

  // 4b. Derived state and memoized values
  const truncatedBio = user?.bio?.slice(0, MAX_BIO_LENGTH);

  // 4c. Event handlers (useCallback for handlers passed to children)
  const handleEditToggle = useCallback(() => {
    setIsEditing(prev => !prev);
  }, []);

  // 4d. Effects
  useEffect(() => {
    if (user && onUpdate) {
      onUpdate(user);
    }
  }, [user, onUpdate]);

  // 4e. Early returns for loading/error states
  if (isLoading) return <div className={styles.skeleton} />;
  if (error) return <div className={styles.error}>{error.message}</div>;
  if (!user) return null;

  // 4f. Main render
  return (
    <div className={`${styles.container} ${className ?? ''}`}>
      <h2 className={styles.name}>{user.name}</h2>
      <p className={styles.bio}>{truncatedBio}</p>
      <Button onClick={handleEditToggle}>
        {isEditing ? 'Cancel' : 'Edit Profile'}
      </Button>
    </div>
  );
};

// 5. Export
export default UserProfile;
```

---

## TypeScript Conventions

```typescript
// ✅ Use interface for object shapes (prefer over type for objects)
interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  createdAt: Date;
}

// ✅ Use type for unions, intersections, and primitives
type UserRole = 'admin' | 'editor' | 'viewer';
type UserId = string;
type ButtonVariant = 'primary' | 'secondary' | 'ghost';

// ✅ Generic utility types
type ApiResponse<T> = {
  data: T;
  status: number;
  message: string;
};

type Optional<T> = T | null | undefined;

// ✅ Avoid `any` — use `unknown` for truly unknown types
const parseResponse = (raw: unknown): User => {
  if (!isUser(raw)) throw new Error('Invalid user shape');
  return raw;
};

// ❌ Avoid
const parseResponse = (raw: any): User => { ... };
```

**Why no `any`:** `any` disables type checking entirely. `unknown` forces you to narrow the type before using it, which catches real bugs. If you're reaching for `any`, consider whether `unknown`, a generic, or a proper interface would work.

---

## Common Patterns

### Conditional class names

```typescript
// ✅ Template literals for simple conditions
<div className={`${styles.card} ${isActive ? styles.active : ''}`}>

// ✅ Array join for multiple conditions
const classes = [
  styles.card,
  isActive && styles.active,
  hasError && styles.error,
  size === 'lg' && styles.large,
].filter(Boolean).join(' ');

<div className={classes}>
```

### Optional chaining and nullish coalescing

```typescript
// ✅ Safe property access
const userName = user?.profile?.displayName ?? 'Anonymous';
const itemCount = cart?.items?.length ?? 0;

// ✅ Optional function calls
onSuccess?.();
onClick?.(event);
```

---

## Anti-Patterns

### ❌ Avoid: Prop drilling more than 2 levels deep

```typescript
// ❌ Drilling theme through 3 levels
<App theme={theme}>
  <Layout theme={theme}>
    <Sidebar theme={theme}>
      <NavItem theme={theme} />  {/* theme never used in Layout or Sidebar */}
```

```typescript
// ✅ Use Context for cross-cutting concerns
const ThemeContext = createContext<Theme>(defaultTheme);

const NavItem = () => {
  const theme = useContext(ThemeContext); // Access directly
};
```

### ❌ Avoid: Inline function definitions in JSX props

```tsx
// ❌ Creates new function reference every render — breaks React.memo
<Button onClick={() => handleDelete(item.id)} />

// ✅ Define handler with useCallback
const handleDelete = useCallback((id: string) => {
  deleteItem(id);
}, [deleteItem]);

<Button onClick={() => handleDelete(item.id)} />
// Or for simple cases:
<Button onClick={handleDelete.bind(null, item.id)} />
```

### ❌ Avoid: Magic numbers

```typescript
// ❌ What is 86400000?
setTimeout(refresh, 86400000);

// ✅ Named constant
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
setTimeout(refresh, ONE_DAY_MS);
```

---

## Tooling & Automation

### `.eslintrc.json`

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:import/recommended",
    "plugin:import/typescript",
    "prettier"
  ],
  "plugins": ["react", "react-hooks", "@typescript-eslint", "import"],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module",
    "ecmaFeatures": { "jsx": true }
  },
  "settings": {
    "react": { "version": "detect" },
    "import/resolver": { "typescript": {} }
  },
  "rules": {
    // Prevent missing React import (not needed in React 17+, but explicit)
    "react/react-in-jsx-scope": "off",
    // Force display names for debugging (helps React DevTools)
    "react/display-name": "warn",
    // Exhaustive deps catches stale closure bugs
    "react-hooks/exhaustive-deps": "error",
    // No any — use unknown or proper types
    "@typescript-eslint/no-explicit-any": "error",
    // Consistent type imports — import type {} when not using runtime value
    "@typescript-eslint/consistent-type-imports": "error",
    // Import ordering enforced
    "import/order": [
      "error",
      {
        "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
        "newlines-between": "always"
      }
    ],
    // No unused variables — catches dead code
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  }
}
```

### `.prettierrc`

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "quoteProps": "as-needed",
  "jsxSingleQuote": false,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### `.vscode/settings.json`

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.validate": ["javascript", "javascriptreact", "typescript", "typescriptreact"]
}
```

---

## Examples

### Complete feature file structure

```
src/features/user-profile/
├── components/
│   ├── UserProfile.tsx         ← Main component
│   ├── UserProfile.test.tsx    ← Co-located tests
│   ├── UserProfile.module.css  ← Scoped styles
│   ├── UserAvatar.tsx          ← Sub-component
│   └── UserAvatar.test.tsx
├── hooks/
│   └── useUserProfile.ts       ← Data fetching hook
├── api/
│   └── userProfileApi.ts       ← API calls
├── types.ts                    ← Feature-local types
└── index.ts                    ← Public API
```

---

## Customization

To adapt these standards:

- **Different quote style:** Change `singleQuote` in `.prettierrc` and the corresponding ESLint rule. Make it consistent — don't mix.
- **Different line length:** Adjust `printWidth`. Shorter (80) improves side-by-side diff readability; longer (120) suits wide monitors.
- **Path aliases:** Configure `compilerOptions.paths` in `tsconfig.json` and mirror in ESLint's `import/resolver`.
- **Monorepo:** Add workspace-level ESLint config with `overrides` per package.

---

## Version and Maintenance

- **Version**: 1.0.0
- **Last Updated**: [date]
- **Review Cycle**: Quarterly
- **Owner**: [team lead or architect]

### Changelog

| Version | Date | Change | Reason |
|---------|------|--------|--------|
| 1.0.0 | [date] | Initial version | Project setup |

### Update Process

1. Open a PR with the proposed change and rationale
2. At least one peer review required
3. Test all code examples in the actual dev environment
4. Update version number and changelog entry
5. Announce breaking changes with migration guidance
