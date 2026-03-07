# Testing Framework Documentation
> Template for `Claude/rules/testing.md`

## Introduction

This document defines testing standards for the React application using **Jest** and **React Testing Library (RTL)**. It covers how to write tests, organize them, mock dependencies, and measure coverage. These standards apply to all component tests, hook tests, integration tests, and utility function tests.

The guiding philosophy: test behavior, not implementation. A test that breaks when you rename an internal variable is fragile. A test that breaks when the user experience changes is valuable.

**Audience:** All developers writing or reviewing tests.

---

## Table of Contents

1. [Test File Organization](#test-file-organization)
2. [Naming Conventions](#naming-conventions)
3. [Component Testing Patterns](#component-testing-patterns)
4. [Hook Testing](#hook-testing)
5. [Async Operations](#async-operations)
6. [Mock Strategies](#mock-strategies)
7. [Integration Tests](#integration-tests)
8. [Error Boundaries](#error-boundaries)
9. [Coverage Requirements](#coverage-requirements)
10. [Anti-Patterns](#anti-patterns)
11. [Tooling & Setup](#tooling--setup)
12. [Customization](#customization)

---

## Test File Organization

Co-locate test files with the source they test:

```
src/features/auth/
├── components/
│   ├── LoginForm.tsx
│   └── LoginForm.test.tsx      ← Co-located
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts         ← Co-located
└── utils/
    ├── validators.ts
    └── validators.test.ts
```

Exception: end-to-end and large integration tests live in a top-level `__tests__/` or `e2e/` directory.

---

## Naming Conventions

```typescript
// File: UserProfile.test.tsx

// Top-level describe = component or function under test
describe('UserProfile', () => {

  // Nested describe = specific scenario or state
  describe('when the user is an admin', () => {

    // it() = specific behavior in plain English
    it('displays the admin badge', () => { ... });
    it('shows the delete button', () => { ... });
  });

  describe('when loading', () => {
    it('renders a skeleton placeholder', () => { ... });
  });

  describe('when an error occurs', () => {
    it('displays the error message', () => { ... });
    it('provides a retry button', () => { ... });
  });
});
```

**Rule:** Test names read as a complete sentence: `UserProfile > when loading > renders a skeleton placeholder`. Never use vague names like `it('works')` or `it('test 1')`.

---

## Component Testing Patterns

### Standard component test

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { UserProfile } from './UserProfile';

// Minimal wrapper for providers your component needs
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('UserProfile', () => {
  const defaultProps = {
    userId: 'user-123',
    onUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user name and bio when data loads successfully', async () => {
    // Arrange
    mockGetUser.mockResolvedValue({ name: 'Alice Smith', bio: 'Engineer' });

    // Act
    renderWithProviders(<UserProfile {...defaultProps} />);

    // Assert
    expect(await screen.findByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Engineer')).toBeInTheDocument();
  });

  it('calls onUpdate when user data changes', async () => {
    const user = userEvent.setup();
    mockGetUser.mockResolvedValue({ name: 'Alice Smith', bio: 'Engineer' });
    renderWithProviders(<UserProfile {...defaultProps} />);

    await screen.findByText('Alice Smith');
    await user.click(screen.getByRole('button', { name: 'Edit Profile' }));

    expect(defaultProps.onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Alice Smith' })
    );
  });

  it('shows skeleton while loading', () => {
    mockGetUser.mockReturnValue(new Promise(() => {})); // Never resolves
    renderWithProviders(<UserProfile {...defaultProps} />);

    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    expect(screen.queryByText('Alice Smith')).not.toBeInTheDocument();
  });

  it('displays error message when fetch fails', async () => {
    mockGetUser.mockRejectedValue(new Error('Network error'));
    renderWithProviders(<UserProfile {...defaultProps} />);

    expect(await screen.findByText('Network error')).toBeInTheDocument();
  });
});
```

### Query priority (most to least preferred)

Use queries in this order — they reflect how users actually interact with the UI:

1. `getByRole` — semantic HTML roles (button, heading, textbox, checkbox)
2. `getByLabelText` — form elements via label
3. `getByPlaceholderText` — input placeholders
4. `getByText` — visible text content
5. `getByDisplayValue` — current form field values
6. `getByAltText` — images
7. `getByTitle` — title attributes
8. `getByTestId` — last resort: `data-testid` attribute

```typescript
// ✅ Preferred — tests that the button has accessible role
screen.getByRole('button', { name: 'Submit' });

// ✅ Also good — form field via label
screen.getByLabelText('Email address');

// ⚠️ Use sparingly — couples test to implementation details
screen.getByTestId('submit-btn');
```

---

## Hook Testing

Use `renderHook` from `@testing-library/react`:

```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('initializes with the provided value', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });

  it('increments the count', () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it('does not exceed maxCount', () => {
    const { result } = renderHook(() => useCounter(9, { maxCount: 10 }));

    act(() => {
      result.current.increment();
      result.current.increment(); // Should be capped at 10
    });

    expect(result.current.count).toBe(10);
  });
});
```

### Testing hooks that use Context

```typescript
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider value={mockAuthContext}>
    {children}
  </AuthProvider>
);

const { result } = renderHook(() => useAuth(), { wrapper });
```

---

## Async Operations

```typescript
import { render, screen, waitFor } from '@testing-library/react';

it('loads and displays search results', async () => {
  const user = userEvent.setup();
  mockSearchApi.mockResolvedValue([
    { id: '1', title: 'First Result' },
    { id: '2', title: 'Second Result' },
  ]);

  render(<SearchPage />);

  await user.type(screen.getByRole('searchbox'), 'react hooks');
  await user.click(screen.getByRole('button', { name: 'Search' }));

  // waitFor polls until assertion passes or times out
  await waitFor(() => {
    expect(screen.getByText('First Result')).toBeInTheDocument();
  });

  expect(screen.getByText('Second Result')).toBeInTheDocument();
  expect(mockSearchApi).toHaveBeenCalledWith('react hooks');
});
```

**Always use `findBy*` or `waitFor` for async — never arbitrary `setTimeout`.**

---

## Mock Strategies

### Mocking API calls (axios/fetch)

```typescript
// __mocks__/axios.ts (auto-mock)
import axios from 'axios';
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  mockedAxios.get.mockResolvedValue({
    data: { users: [{ id: '1', name: 'Alice' }] },
    status: 200,
  });
});
```

### Mocking a module

```typescript
// Mock entire module
jest.mock('../api/userApi', () => ({
  getUser: jest.fn(),
  updateUser: jest.fn(),
}));

import { getUser } from '../api/userApi';
const mockGetUser = getUser as jest.MockedFunction<typeof getUser>;

beforeEach(() => {
  mockGetUser.mockResolvedValue({ id: '1', name: 'Alice' });
});
```

### Mocking Context

```typescript
const mockAuthContext = {
  user: { id: 'user-1', name: 'Alice', role: 'admin' },
  logout: jest.fn(),
  isAuthenticated: true,
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
}));
```

### Mocking custom hooks

```typescript
jest.mock('./useUserData', () => ({
  useUserData: jest.fn(() => ({
    user: { id: '1', name: 'Alice' },
    isLoading: false,
    error: null,
  })),
}));
```

### Mocking `IntersectionObserver` and other browser APIs

```typescript
// jest.setup.ts
const mockIntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: mockIntersectionObserver,
});
```

---

## Integration Tests

Integration tests verify that components work together correctly. They use real implementations rather than mocks where feasible.

```typescript
// LoginFlow.integration.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../mocks/server'; // MSW mock server
import { http, HttpResponse } from 'msw';

import { App } from '../App';

describe('Login flow', () => {
  it('redirects to dashboard after successful login', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email'), 'alice@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Log in' }));

    expect(await screen.findByText('Welcome, Alice')).toBeInTheDocument();
    expect(screen.queryByText('Log in')).not.toBeInTheDocument();
  });

  it('shows error when credentials are invalid', async () => {
    server.use(
      http.post('/api/auth/login', () =>
        HttpResponse.json({ message: 'Invalid credentials' }, { status: 401 })
      )
    );
    const user = userEvent.setup();

    render(<MemoryRouter initialEntries={['/login']}><App /></MemoryRouter>);

    await user.type(screen.getByLabelText('Email'), 'wrong@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrong');
    await user.click(screen.getByRole('button', { name: 'Log in' }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
  });
});
```

**Recommended:** Use [MSW (Mock Service Worker)](https://mswjs.io/) for API mocking in integration tests. It intercepts at the network level, making tests closer to reality.

---

## Error Boundaries

```typescript
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) throw new Error('Component crash!');
  return <div>Normal render</div>;
};

describe('ErrorBoundary', () => {
  // Suppress console.error for expected errors
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary fallback={<div>Error occurred</div>}>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Normal render')).toBeInTheDocument();
  });

  it('renders fallback UI when a child throws', () => {
    render(
      <ErrorBoundary fallback={<div>Error occurred</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });
});
```

---

## Coverage Requirements

| Metric | Minimum |
|--------|---------|
| Statements | 80% |
| Branches | 80% |
| Functions | 80% |
| Lines | 80% |

Configure in `jest.config.ts`:

```typescript
// jest.config.ts
import type { Config } from 'jest';

const config: Config = {
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80,
    },
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/**/*.stories.tsx',
    '!src/mocks/**',
  ],
};

export default config;
```

---

## Anti-Patterns

### ❌ Avoid: Testing implementation details

```typescript
// ❌ Couples test to internal state — breaks on refactor
const component = shallow(<LoginForm />);
expect(component.state('email')).toBe('');
expect(component.find('input[name="email"]').prop('onChange')).toBeDefined();

// ✅ Test user-visible behavior
render(<LoginForm />);
expect(screen.getByLabelText('Email')).toHaveValue('');
```

### ❌ Avoid: `act()` warnings from not awaiting async events

```typescript
// ❌ State update happens asynchronously — will warn
fireEvent.click(button);
expect(screen.getByText('Success')).toBeInTheDocument();

// ✅ Wait for the update
await user.click(button);
expect(await screen.findByText('Success')).toBeInTheDocument();
```

### ❌ Avoid: Snapshots for complex components

```typescript
// ❌ Snapshot tests break on any change, even irrelevant ones
expect(render(<UserProfile />)).toMatchSnapshot();

// ✅ Assert on specific meaningful properties
expect(screen.getByRole('heading')).toHaveTextContent('Alice Smith');
expect(screen.getByRole('button', { name: 'Edit' })).toBeEnabled();
```

---

## Tooling & Setup

### `jest.config.ts`

```typescript
import type { Config } from 'jest';

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { tsconfig: 'tsconfig.test.json' }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.module\\.css$': 'identity-obj-proxy',
    '\\.(css|less|scss)$': '<rootDir>/__mocks__/styleMock.ts',
  },
  coverageThreshold: {
    global: { statements: 80, branches: 80, functions: 80, lines: 80 },
  },
};

export default config;
```

### `jest.setup.ts`

```typescript
import '@testing-library/jest-dom';
import { server } from './src/mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### `package.json` scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watchAll",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --watchAll=false"
  }
}
```

---

## Customization

- **Different coverage threshold:** Adjust per-directory thresholds if some modules (like configuration files) can't be meaningfully tested.
- **Vitest instead of Jest:** The patterns are identical — swap `jest.fn()` for `vi.fn()` and the config format changes slightly.
- **Storybook integration:** Use `@storybook/testing-library` to reuse stories as test fixtures.
- **Playwright/Cypress for E2E:** Complement unit/integration tests — don't replace them. E2E tests catch integration issues; unit tests give faster feedback loops.

---

## Version and Maintenance

- **Version**: 1.0.0
- **Last Updated**: [date]
- **Review Cycle**: Quarterly
- **Owner**: [team lead]

### Changelog

| Version | Date | Change | Reason |
|---------|------|--------|--------|
| 1.0.0 | [date] | Initial version | Project setup |
