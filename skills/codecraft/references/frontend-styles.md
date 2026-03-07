# Component Styling Conventions
> Template for `Claude/rules/frontend/styles.md`

## Introduction

This document defines how to write styles for React components. It covers the three primary styling approaches — CSS Modules, styled-components/emotion, and Tailwind CSS — with guidance on when to use each, how to structure them, and how to maintain consistency at scale.

The core principle: styles should be scoped, predictable, and collocated with the component they style. Global styles are the exception, not the rule.

**Audience:** All developers writing component styles or layout CSS.

---

## Table of Contents

1. [Choosing a Styling Approach](#choosing-a-styling-approach)
2. [CSS Modules](#css-modules)
3. [CSS-in-JS (styled-components / emotion)](#css-in-js)
4. [Tailwind CSS](#tailwind-css)
5. [Global Styles & Variables](#global-styles--variables)
6. [Responsive Design](#responsive-design)
7. [Theming](#theming)
8. [Naming Conventions](#naming-conventions)
9. [Common Patterns](#common-patterns)
10. [Anti-Patterns](#anti-patterns)
11. [Tooling](#tooling)
12. [Customization](#customization)

---

## Choosing a Styling Approach

| Approach | Best for | Avoid when |
|----------|---------|------------|
| **CSS Modules** | Teams familiar with CSS; build performance priority | Dynamic styles based on many JS values |
| **styled-components/emotion** | Dynamic styles; design systems; TypeScript-first teams | Large bundle size is a concern |
| **Tailwind CSS** | Rapid prototyping; utility-first; design system constraints | Teams new to utility CSS; highly custom designs |

**Default recommendation:** CSS Modules. Zero runtime overhead, full CSS features, works with every build tool, and forces explicit naming.

Mixing approaches is acceptable — for example, Tailwind for layout/spacing, CSS Modules for component-specific styles. What matters is consistency within a feature.

---

## CSS Modules

CSS Modules scope class names to the component by default. No naming collisions across files.

### Basic usage

```tsx
// Button.module.css
.button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.button--primary {
  background-color: var(--color-primary);
  color: var(--color-white);
}

.button--secondary {
  background-color: transparent;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}

.button--sm { padding: 0.25rem 0.75rem; font-size: 0.875rem; }
.button--lg { padding: 0.75rem 1.5rem; font-size: 1.125rem; }

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

```tsx
// Button.tsx
import styles from './Button.module.css';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const Button = ({ variant = 'primary', size = 'md', disabled, children, onClick }: ButtonProps) => {
  const classes = [
    styles.button,
    styles[`button--${variant}`],
    size !== 'md' && styles[`button--${size}`],
  ].filter(Boolean).join(' ');

  return (
    <button className={classes} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
};
```

### Composing classes

```tsx
// ✅ Compose external className with internal styles
interface CardProps {
  children: React.ReactNode;
  className?: string; // Allow callers to extend styles
}

const Card = ({ children, className }: CardProps) => (
  <div className={`${styles.card} ${className ?? ''}`.trim()}>
    {children}
  </div>
);
```

### Global class override (when necessary)

```css
/* Button.module.css */
.button :global(.icon) {
  /* Targets a child with class "icon" without scoping */
  width: 1em;
  height: 1em;
}
```

---

## CSS-in-JS

Use styled-components or emotion when styles have many dynamic values driven by JavaScript state.

```tsx
// ✅ styled-components example
import styled, { css } from 'styled-components';

interface ButtonStyleProps {
  $variant: 'primary' | 'secondary';
  $size: 'sm' | 'md' | 'lg';
}

// $ prefix for transient props (not forwarded to DOM)
const StyledButton = styled.button<ButtonStyleProps>`
  display: inline-flex;
  align-items: center;
  font-weight: 500;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 150ms ease;

  ${({ $size }) => $size === 'sm' && css`padding: 0.25rem 0.75rem; font-size: 0.875rem;`}
  ${({ $size }) => $size === 'md' && css`padding: 0.5rem 1rem; font-size: 1rem;`}
  ${({ $size }) => $size === 'lg' && css`padding: 0.75rem 1.5rem; font-size: 1.125rem;`}

  ${({ $variant, theme }) =>
    $variant === 'primary'
      ? css`background: ${theme.colors.primary}; color: ${theme.colors.white};`
      : css`background: transparent; border: 1px solid ${theme.colors.primary}; color: ${theme.colors.primary};`
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const Button = ({ variant = 'primary', size = 'md', ...props }) => (
  <StyledButton $variant={variant} $size={size} {...props} />
);
```

### Theme integration

```tsx
// theme.ts
export const theme = {
  colors: {
    primary: '#6366f1',
    primaryDark: '#4f46e5',
    white: '#ffffff',
    gray100: '#f3f4f6',
    gray900: '#111827',
    error: '#ef4444',
    success: '#22c55e',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    full: '9999px',
  },
} as const;

export type Theme = typeof theme;

// App.tsx
import { ThemeProvider } from 'styled-components';
<ThemeProvider theme={theme}><App /></ThemeProvider>
```

---

## Tailwind CSS

Tailwind provides constraint-based utility classes. Best for rapid development when the design system fits within Tailwind's defaults.

```tsx
// ✅ Basic Tailwind usage
const Button = ({ variant = 'primary', disabled, children, onClick }: ButtonProps) => {
  const baseClasses = 'inline-flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors';
  const variantClasses = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
    secondary: 'border border-indigo-600 text-indigo-600 hover:bg-indigo-50',
    ghost: 'text-gray-700 hover:bg-gray-100',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

// ✅ Use clsx or tailwind-merge for conditional classes
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const cx = (...inputs: Parameters<typeof clsx>) => twMerge(clsx(inputs));

const Button = ({ variant, disabled, className, children }) => (
  <button
    className={cx(
      'inline-flex items-center px-4 py-2 rounded-md font-medium',
      variant === 'primary' && 'bg-indigo-600 text-white hover:bg-indigo-700',
      variant === 'secondary' && 'border border-indigo-600 text-indigo-600',
      disabled && 'opacity-50 cursor-not-allowed',
      className // User-provided classes override defaults via twMerge
    )}
  >
    {children}
  </button>
);
```

### Custom config

```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#6366f1', dark: '#4f46e5', light: '#a5b4fc' },
        brand: { /* your brand colors */ },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
export default config;
```

---

## Global Styles & Variables

### CSS custom properties (variables)

Define design tokens as CSS variables for consistency and easy theming:

```css
/* styles/variables.css */
:root {
  /* Colors */
  --color-primary: #6366f1;
  --color-primary-dark: #4f46e5;
  --color-primary-light: #a5b4fc;
  --color-error: #ef4444;
  --color-success: #22c55e;
  --color-warning: #f59e0b;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Border radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);

  /* Z-index scale */
  --z-dropdown: 100;
  --z-modal: 200;
  --z-toast: 300;
}

/* Dark mode */
[data-theme='dark'] {
  --color-primary: #818cf8;
  /* ... dark mode overrides */
}
```

```css
/* styles/globals.css */
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: 1.5;
  color: var(--color-text);
  background-color: var(--color-background);
}

/* Utility: visually hidden but accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

## Responsive Design

Use a mobile-first approach. Define breakpoints as CSS variables or Tailwind config:

```css
/* Breakpoints (mobile-first) */
/* sm: 640px, md: 768px, lg: 1024px, xl: 1280px */

.card-grid {
  display: grid;
  grid-template-columns: 1fr;           /* mobile: 1 column */
  gap: var(--space-4);
}

@media (min-width: 640px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .card-grid { grid-template-columns: repeat(3, 1fr); }
}
```

```tsx
// ✅ Responsive hook (avoid where CSS can handle it)
const useBreakpoint = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);
  useEffect(() => {
    const query = window.matchMedia('(max-width: 639px)');
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    query.addEventListener('change', handler);
    return () => query.removeEventListener('change', handler);
  }, []);
  return { isMobile };
};
// Only use this when layout logic genuinely needs JS — prefer CSS media queries
```

---

## Naming Conventions

Follow BEM (Block Element Modifier) for CSS Modules:

```css
/* Block: the component */
.card { }

/* Element: a part of the block (double underscore) */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier: a variant (double dash) */
.card--elevated { }
.card--compact { }
.card__header--sticky { }
```

```tsx
// ✅ In JSX, reference class names directly — don't construct them dynamically
<div className={styles.card}>
  <div className={styles.card__header}>
  </div>
</div>

// ❌ Avoid dynamic class name construction that breaks CSS Modules tree-shaking
const el = styles[`card__${partName}`]; // Opaque — hard to trace
```

---

## Common Patterns

### Conditional class composition

```tsx
// ✅ Using array filter + join
const alertClasses = [
  styles.alert,
  styles[`alert--${type}`],     // 'success', 'error', 'warning'
  isVisible && styles.visible,
  isDismissible && styles.dismissible,
].filter(Boolean).join(' ');

// ✅ Using clsx (install: npm i clsx)
import { clsx } from 'clsx';

const alertClasses = clsx(
  styles.alert,
  {
    [styles['alert--success']]: type === 'success',
    [styles['alert--error']]: type === 'error',
    [styles.visible]: isVisible,
  }
);
```

### Animation

```css
/* ✅ Prefer CSS transitions and keyframes over JS animation for performance */
.modal {
  opacity: 0;
  transform: translateY(-8px);
  transition: opacity 200ms ease, transform 200ms ease;
}

.modal--visible {
  opacity: 1;
  transform: translateY(0);
}

/* ✅ Respect motion preferences */
@media (prefers-reduced-motion: reduce) {
  .modal {
    transition: none;
  }
}
```

---

## Anti-Patterns

### ❌ Inline styles for anything other than truly dynamic values

```tsx
// ❌ Inline styles are hard to maintain, can't use media queries, pseudo-selectors
<div style={{ display: 'flex', padding: '16px', backgroundColor: '#6366f1' }}>

// ✅ Use CSS classes
<div className={styles.container}>

// ✅ Inline styles are OK ONLY for values that genuinely require runtime computation
<div style={{ width: `${progress}%` }}>  // Fine — dynamic value
```

### ❌ Relying on global class name collisions

```css
/* ❌ Global class names pollute every component */
.button { ... }   /* In globals.css — affects every .button everywhere */

/* ✅ Scope to the component via CSS Modules */
/* Button.module.css */
.button { ... }   /* Scoped — won't conflict */
```

### ❌ Hardcoded pixel values instead of design tokens

```css
/* ❌ One-off magic numbers */
.card { padding: 14px; border-radius: 7px; }

/* ✅ Use your CSS variable scale */
.card { padding: var(--space-4); border-radius: var(--radius-md); }
```

---

## Tooling

### PostCSS (for CSS Modules projects)

```javascript
// postcss.config.js
module.exports = {
  plugins: [
    require('postcss-modules'),
    require('autoprefixer'),
    require('postcss-custom-media'), // If using custom media queries
  ],
};
```

### Stylelint

```json
// .stylelintrc.json
{
  "extends": ["stylelint-config-standard", "stylelint-config-css-modules"],
  "rules": {
    "color-no-invalid-hex": true,
    "unit-allowed-list": ["rem", "em", "%", "px", "vh", "vw", "fr", "deg", "ms", "s"],
    "declaration-no-important": true,
    "selector-class-pattern": "^[a-z][a-z0-9]*(__[a-z][a-z0-9]*)?(--[a-z][a-z0-9]*)?$"
  }
}
```

---

## Customization

- **If using Tailwind exclusively:** Remove CSS Modules patterns, keep the variables section for any custom CSS you still need.
- **If using styled-components:** Add `babel-plugin-styled-components` for better debugging (readable class names and server-side rendering support).
- **Dark mode:** Use `data-theme` attribute on `<html>` rather than class to avoid flash-of-unstyled-content (FOUC) on page load.
- **CSS-in-JS with SSR (Next.js):** styled-components requires `ServerStyleSheet`; emotion requires `@emotion/server`. Add to your server rendering setup.

---

## Version and Maintenance

- **Version**: 1.0.0
- **Last Updated**: [date]
- **Review Cycle**: Quarterly
- **Owner**: [team lead or design systems owner]

### Changelog

| Version | Date | Change | Reason |
|---------|------|--------|--------|
| 1.0.0 | [date] | Initial version | Project setup |
