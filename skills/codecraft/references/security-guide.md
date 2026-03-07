# Frontend Security Protocols
> Template for `Claude/rules/security.md`

## Introduction

This document defines security standards for the React frontend. It addresses the most common frontend vulnerabilities: XSS, CSRF, insecure data storage, and improper API communication. These standards align with the [OWASP Top 10](https://owasp.org/www-project-top-ten/) and React-specific security advisories.

Security is not a phase — it is a continuous practice embedded in code review, dependency management, and deployment. Every developer is responsible for applying these standards before submitting code.

**Audience:** All developers, including those writing tests, configuring CI/CD, and reviewing pull requests.

---

## Table of Contents

1. [XSS Prevention](#xss-prevention)
2. [Input Validation](#input-validation)
3. [Secure API Communication](#secure-api-communication)
4. [Authentication & Token Handling](#authentication--token-handling)
5. [React-Specific Vulnerabilities](#react-specific-vulnerabilities)
6. [Dependency Security](#dependency-security)
7. [Security Checklist](#security-checklist)
8. [Anti-Patterns](#anti-patterns)
9. [Tooling & Automation](#tooling--automation)
10. [Customization](#customization)

---

## XSS Prevention

Cross-Site Scripting (XSS) is the most common frontend vulnerability. An attacker injects malicious scripts that run in a victim's browser under your domain's trust.

### React's built-in protections

React escapes string values in JSX automatically:

```tsx
// ✅ Safe — React escapes this before insertion into the DOM
const userInput = '<script>alert("xss")</script>';
return <div>{userInput}</div>;
// Renders as visible text, not executable script
```

This only applies to JSX string interpolation. Several escape hatches bypass it.

### dangerouslySetInnerHTML — use sparingly with sanitization

```tsx
import DOMPurify from 'dompurify';

// ❌ Never inject unsanitized HTML
const RichText = ({ html }: { html: string }) => (
  <div dangerouslySetInnerHTML={{ __html: html }} />  // DANGEROUS
);

// ✅ Sanitize before injecting
const RichText = ({ html }: { html: string }) => {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'title', 'rel'],
    FORCE_HTTPS: true,
  });
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};
```

**Install:** `npm install dompurify && npm install --save-dev @types/dompurify`

### Output encoding for dynamic content

```tsx
// ✅ For URLs — validate scheme before rendering
const SafeLink = ({ url, children }: { url: string; children: React.ReactNode }) => {
  const isAllowed = /^https?:\/\//.test(url);
  if (!isAllowed) {
    console.warn(`Blocked unsafe URL: ${url}`);
    return <span>{children}</span>;
  }
  return <a href={url} rel="noopener noreferrer">{children}</a>;
};

// ❌ Never do this — allows javascript: URLs
<a href={userProvidedUrl}>Click me</a>
```

---

## Input Validation

Validate at the point of user input, not just before API calls.

```tsx
// ✅ Form validation with zod
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const loginSchema = z.object({
  email: z.string()
    .email('Must be a valid email address')
    .max(255, 'Email must be under 255 characters'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password must be under 128 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    // data is validated and typed — safe to send
    authApi.login(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} type="email" />
      {errors.email && <span>{errors.email.message}</span>}

      <input {...register('password')} type="password" />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit">Log in</button>
    </form>
  );
};
```

### Rate limiting at the client level

The server enforces rate limits, but the client should also throttle rapid submissions to reduce unintentional abuse:

```tsx
import { useCallback, useRef } from 'react';

const useThrottledSubmit = (fn: () => void, limitMs = 2000) => {
  const lastCall = useRef<number>(0);
  return useCallback(() => {
    const now = Date.now();
    if (now - lastCall.current > limitMs) {
      lastCall.current = now;
      fn();
    }
  }, [fn, limitMs]);
};
```

---

## Secure API Communication

### Axios instance with security defaults

```typescript
// src/lib/apiClient.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL, // Always use env var — never hardcode
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest', // CSRF signal for some backends
  },
  withCredentials: true, // Required for httpOnly cookie auth
});

// Attach auth token from memory (not localStorage — see token section)
apiClient.interceptors.request.use(config => {
  const token = tokenStore.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — token expired, redirect to login
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      tokenStore.clearToken();
      window.location.replace('/login');
    }
    return Promise.reject(error);
  }
);
```

### Validate response shape

Never trust API responses blindly. Validate with zod at the API layer:

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().max(200),
  email: z.string().email(),
  role: z.enum(['admin', 'editor', 'viewer']),
});

export const getUser = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`);
  return UserSchema.parse(response.data); // Throws if shape doesn't match
};
```

---

## Authentication & Token Handling

### Storage trade-offs

| Method | XSS Risk | CSRF Risk | Recommendation |
|--------|----------|-----------|----------------|
| localStorage | High — JS-accessible | None | Avoid for sensitive tokens |
| sessionStorage | High — JS-accessible | None | Better than localStorage, still risky |
| httpOnly cookie | None — not JS-accessible | Requires CSRF token | Preferred for authentication |
| In-memory (React state) | Low — lost on refresh | None | Good for short-lived tokens |

**Recommended approach:** Store long-lived refresh tokens in httpOnly cookies (set by the server). Store short-lived access tokens in memory only.

### In-memory token store

```typescript
// src/lib/tokenStore.ts
// Access tokens live in memory — cleared on page refresh
// Refresh tokens live in httpOnly cookies — inaccessible to JS
let accessToken: string | null = null;

export const tokenStore = {
  getToken: () => accessToken,
  setToken: (token: string) => { accessToken = token; },
  clearToken: () => { accessToken = null; },
};
```

### Token refresh flow

```typescript
// src/lib/apiClient.ts — add refresh logic
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve(token!);
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post('/auth/refresh', {}, { withCredentials: true });
        tokenStore.setToken(data.accessToken);
        processQueue(null, data.accessToken);
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        tokenStore.clearToken();
        window.location.replace('/login');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

---

## React-Specific Vulnerabilities

### Server-Side Rendering (SSR) injection

When serializing state for SSR hydration, escape JSON properly:

```tsx
// ❌ Vulnerable — if JSON contains </script>, this breaks
<script>window.__INITIAL_STATE__ = {JSON.stringify(state)}</script>

// ✅ Escape closing tags
const safeJSON = JSON.stringify(state).replace(/</g, '\\u003c');
<script dangerouslySetInnerHTML={{ __html: `window.__INITIAL_STATE__ = ${safeJSON}` }} />
```

### Third-party component security

Before adding any npm package:

1. Check last publish date (unmaintained packages accumulate CVEs)
2. Check weekly downloads (low = less community scrutiny)
3. Run `npm audit` after install
4. Pin exact versions for security-sensitive packages (`1.2.3` not `^1.2.3`)

```json
{
  "dependencies": {
    "dompurify": "3.0.6",   // Pinned — security-critical
    "react": "^18.2.0"      // Range OK — React team maintains
  }
}
```

---

## Security Checklist

Use this checklist during code review for any feature involving user input, authentication, or API calls:

### Code Review Checklist

- [ ] No `dangerouslySetInnerHTML` without DOMPurify sanitization
- [ ] No user-provided values used in `href` without URL scheme validation
- [ ] All form inputs validated with a schema (zod, yup, or similar)
- [ ] Sensitive tokens not stored in localStorage or sessionStorage
- [ ] All API calls go through the secure `apiClient` instance (not raw fetch/axios)
- [ ] Environment variables used for all API URLs and secrets (no hardcoded values)
- [ ] Response data validated before use
- [ ] No `eval()`, `new Function()`, or `setTimeout(string)` calls
- [ ] All external links have `rel="noopener noreferrer"`
- [ ] New npm packages audited before merge

### Deployment Checklist

- [ ] `npm audit --audit-level=moderate` passes with no failures
- [ ] Security headers configured: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- [ ] HTTPS enforced — no HTTP endpoints in production
- [ ] Source maps not exposed to public in production
- [ ] Error messages don't expose internal details (stack traces, file paths)

---

## Anti-Patterns

### ❌ Using localStorage for auth tokens

```typescript
// ❌ Any XSS attack can steal this
localStorage.setItem('authToken', token);

// ✅ Keep in memory; use httpOnly cookies for persistence
tokenStore.setToken(token); // In-memory, gone on refresh
// Server sets httpOnly refresh cookie
```

### ❌ Constructing URLs from user input

```typescript
// ❌ Open redirect — attacker controls destination
const redirect = new URLSearchParams(window.location.search).get('redirect');
window.location.href = redirect; // Could be https://evil.com

// ✅ Validate against an allowlist
const ALLOWED_PATHS = ['/dashboard', '/profile', '/settings'];
const redirect = new URLSearchParams(window.location.search).get('redirect');
const safePath = ALLOWED_PATHS.includes(redirect ?? '') ? redirect : '/dashboard';
navigate(safePath);
```

### ❌ Logging sensitive data

```typescript
// ❌ Tokens/passwords appear in browser console and log aggregators
console.log('User logged in:', { user, token, password });

// ✅ Log only non-sensitive identifiers
console.log('User logged in:', { userId: user.id });
```

---

## Tooling & Automation

### `npm audit` in CI

```yaml
# .github/workflows/ci.yml (partial)
- name: Security audit
  run: npm audit --audit-level=moderate
```

### ESLint security plugin

```bash
npm install --save-dev eslint-plugin-security eslint-plugin-no-secrets
```

```json
// .eslintrc.json additions
{
  "plugins": ["security", "no-secrets"],
  "rules": {
    "security/detect-object-injection": "warn",
    "security/detect-non-literal-regexp": "warn",
    "no-secrets/no-secrets": "error"
  }
}
```

### Content Security Policy (set in server/proxy config)

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.yourdomain.com;
  frame-ancestors 'none';
```

---

## Customization

- **If using httpOnly cookies exclusively:** Remove the in-memory token store pattern. Ensure your server sets `SameSite=Strict` and `Secure` on all auth cookies.
- **If using OAuth/OIDC:** Store the access token in memory, handle PKCE flow for SPAs, and never expose `client_secret` in frontend code.
- **If using GraphQL:** Add query depth limiting on the server and validate that mutations require authentication headers.

---

## Version and Maintenance

- **Version**: 1.0.0
- **Last Updated**: [date]
- **Review Cycle**: Quarterly (or after any security advisory)
- **Owner**: [security lead or team lead]

### Changelog

| Version | Date | Change | Reason |
|---------|------|--------|--------|
| 1.0.0 | [date] | Initial version | Project setup |
