# React-Specific Guidelines
> Template for `Claude/rules/frontend/React.md`

## Introduction

This document covers React-specific patterns beyond general code style. It defines how to use hooks correctly, manage component lifecycle, handle state, and optimize performance. These guidelines assume React 18+ and function components throughout — class components are not used in new code.

The core principle: React is a UI library, not a full framework. Keep components focused on rendering. Push business logic into hooks and utilities.

**Audience:** All developers writing React components or hooks.

---

## Table of Contents

1. [Hook Patterns](#hook-patterns)
2. [Component Lifecycle](#component-lifecycle)
3. [State Management](#state-management)
4. [Performance Optimization](#performance-optimization)
5. [Prop Validation](#prop-validation)
6. [Error Boundaries](#error-boundaries)
7. [Common Patterns](#common-patterns)
8. [Anti-Patterns](#anti-patterns)
9. [Tooling](#tooling)
10. [Customization](#customization)

---

## Hook Patterns

### useState

```tsx
// ✅ Simple scalar values
const [isOpen, setIsOpen] = useState(false);
const [count, setCount] = useState(0);

// ✅ Grouped related state into objects
const [formState, setFormState] = useState({
  name: '',
  email: '',
  role: 'viewer' as UserRole,
});

// ✅ Functional updater for state that depends on previous value
const increment = () => setCount(prev => prev + 1);

// ✅ Lazy initializer for expensive initial state
const [data, setData] = useState<Data[]>(() => {
  return JSON.parse(localStorage.getItem('cache') ?? '[]');
});

// ❌ Avoid mirroring props in state — creates sync issues
const BadComponent = ({ initialValue }: { initialValue: number }) => {
  const [value, setValue] = useState(initialValue); // Won't update if prop changes
};

// ✅ Derive from props directly, or use key to reset
const GoodComponent = ({ value }: { value: number }) => {
  const doubled = value * 2; // Derived — always in sync
};
```

### useEffect

```tsx
// ✅ Dependency array must be complete — include every reactive value used inside
useEffect(() => {
  document.title = `${user.name} — Dashboard`;
}, [user.name]); // Only re-runs when user.name changes

// ✅ Cleanup subscriptions and timers
useEffect(() => {
  const subscription = eventBus.subscribe('update', handleUpdate);
  return () => subscription.unsubscribe(); // Cleanup on unmount or re-run
}, [handleUpdate]);

// ✅ Fetch data with abort controller for cancellation
useEffect(() => {
  const controller = new AbortController();

  const fetchData = async () => {
    try {
      const response = await fetch(`/api/users/${userId}`, {
        signal: controller.signal,
      });
      if (!response.ok) throw new Error('Fetch failed');
      setUser(await response.json());
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        setError(error);
      }
    }
  };

  fetchData();
  return () => controller.abort(); // Cancel pending request on unmount
}, [userId]);

// ❌ Don't use useEffect for things that don't need it
// Event handlers, computed values, and user interactions don't need effects
const BadFilter = ({ items, query }) => {
  const [filtered, setFiltered] = useState(items);
  useEffect(() => {
    setFiltered(items.filter(item => item.name.includes(query)));
  }, [items, query]); // Unnecessary — causes extra render
};

// ✅ Compute during render instead
const GoodFilter = ({ items, query }) => {
  const filtered = items.filter(item => item.name.includes(query)); // No effect needed
};
```

### useContext

```tsx
// ✅ Create typed context with a meaningful default
interface AuthContextValue {
  user: User | null;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ✅ Custom hook that enforces usage within provider
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// ✅ Provider component
export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, logout, isAuthenticated: user !== null }),
    [user, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

### useReducer

Use `useReducer` over `useState` when state has multiple sub-values that transition together, or when the next state depends on complex logic.

```tsx
type State = {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: User[] | null;
  error: string | null;
};

type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: User[] }
  | { type: 'FETCH_ERROR'; payload: string };

const initialState: State = { status: 'idle', data: null, error: null };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, status: 'loading', error: null };
    case 'FETCH_SUCCESS':
      return { status: 'success', data: action.payload, error: null };
    case 'FETCH_ERROR':
      return { status: 'error', data: null, error: action.payload };
    default:
      return state;
  }
}

const UserList = () => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const fetchUsers = async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const users = await userApi.getAll();
      dispatch({ type: 'FETCH_SUCCESS', payload: users });
    } catch (error) {
      dispatch({ type: 'FETCH_ERROR', payload: 'Failed to load users' });
    }
  };

  // render based on state.status
};
```

### useMemo and useCallback

Memoize to prevent unnecessary recalculations and referential inequality — not by default, only when there's a measured cost.

```tsx
// ✅ useMemo: expensive computation that should not re-run on every render
const sortedAndFilteredUsers = useMemo(
  () =>
    users
      .filter(u => u.role === selectedRole)
      .sort((a, b) => a.name.localeCompare(b.name)),
  [users, selectedRole]
);

// ✅ useCallback: stable function reference for memoized child components
const handleItemSelect = useCallback(
  (itemId: string) => {
    setSelectedId(itemId);
    onSelect?.(itemId);
  },
  [onSelect] // onSelect from props — include it
);

// ❌ Don't memoize cheap operations — overhead outweighs benefit
const badMemo = useMemo(() => a + b, [a, b]); // Addition doesn't need memoization
const badCallback = useCallback(() => setValue(true), []); // Not passed to memoized child
```

### useRef

```tsx
// ✅ DOM access
const inputRef = useRef<HTMLInputElement>(null);
const focusInput = () => inputRef.current?.focus();

// ✅ Persisting values across renders without triggering re-render
const lastScrollPosition = useRef(0);
const intervalId = useRef<ReturnType<typeof setInterval>>();

// ✅ Storing previous value
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}
```

---

## Component Lifecycle

### Mounting

```tsx
const UserProfile = ({ userId }: { userId: string }) => {
  // Runs once on mount (empty dependency array)
  useEffect(() => {
    analytics.track('profile_viewed', { userId });
    return () => {
      analytics.track('profile_exited', { userId });
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps — intentional mount-only
};
```

### Updating

```tsx
// Run effect when specific values change
useEffect(() => {
  if (userId !== previousUserId) {
    resetLocalState();
  }
}, [userId]);

// Better: use key prop to reset entire component tree
<UserProfile key={userId} userId={userId} />
// React unmounts and remounts when key changes — cleanest reset pattern
```

### Unmounting

```tsx
useEffect(() => {
  const handler = (event: KeyboardEvent) => {
    if (event.key === 'Escape') onClose();
  };
  document.addEventListener('keydown', handler);

  return () => {
    document.removeEventListener('keydown', handler); // Always clean up
  };
}, [onClose]);
```

---

## State Management

Choose based on scope and complexity:

| Scenario | Approach |
|----------|---------|
| Component-local UI state | `useState` / `useReducer` |
| Shared state between siblings | Lift state to common parent |
| Cross-cutting app state (auth, theme) | Context API |
| Complex global state with many updates | Zustand or Redux Toolkit |
| Server state / data fetching | React Query or SWR |

### Context API — when and how

Context is for state that changes infrequently and is needed across many components (theme, auth, locale). It is not a replacement for a state management library.

```tsx
// ✅ Split contexts by update frequency to avoid unnecessary re-renders
// Theme changes rarely — fine in context
// User action state changes often — use local state or a library

const ThemeContext = createContext<Theme>(defaultTheme);    // Rarely changes
const UserContext = createContext<User | null>(null);       // Changes on login/logout
// Don't combine these — every ThemeContext consumer re-renders on user change
```

---

## Performance Optimization

### React.memo

Prevents re-rendering when props haven't changed:

```tsx
// ✅ Wrap components that receive stable props but re-render due to parent changes
const UserCard = React.memo(({ user, onSelect }: UserCardProps) => {
  return (
    <div onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
    </div>
  );
});

// Memo only works if props are referentially stable
// Combine with useCallback for function props and useMemo for object props
```

### Code splitting and lazy loading

```tsx
import { lazy, Suspense } from 'react';

// ✅ Route-level code splitting — loads bundle only when route is visited
const Dashboard = lazy(() => import('./features/dashboard/Dashboard'));
const Settings = lazy(() => import('./features/settings/Settings'));

const App = () => (
  <Routes>
    <Route
      path="/dashboard"
      element={
        <Suspense fallback={<PageSkeleton />}>
          <Dashboard />
        </Suspense>
      }
    />
    <Route
      path="/settings"
      element={
        <Suspense fallback={<PageSkeleton />}>
          <Settings />
        </Suspense>
      }
    />
  </Routes>
);
```

### Virtualization for large lists

Render only visible items when lists exceed ~100 items:

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualList = ({ items }: { items: Item[] }) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // Estimated row height in pixels
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <ItemRow item={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## Prop Validation

### TypeScript interfaces (preferred)

```tsx
interface ButtonProps {
  // Required props
  label: string;
  onClick: () => void;
  // Optional props with defaults documented in destructuring
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  isLoading?: boolean;
  // Children
  children?: React.ReactNode;
  // Allow additional HTML attributes
  className?: string;
}

const Button = ({
  label,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  isLoading = false,
  children,
  className,
}: ButtonProps) => { ... };
```

### PropTypes (JavaScript projects)

```jsx
import PropTypes from 'prop-types';

const Button = ({ label, onClick, variant, size, disabled }) => { ... };

Button.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'ghost']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
};

Button.defaultProps = {
  variant: 'primary',
  size: 'md',
  disabled: false,
};
```

---

## Error Boundaries

Error boundaries catch rendering errors and prevent the whole app from crashing:

```tsx
import { Component, ErrorInfo } from 'react';

interface Props {
  fallback: React.ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to error tracking service (Sentry, Datadog, etc.)
    errorTracker.captureException(error, { extra: errorInfo });
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Usage: wrap each major section independently
<ErrorBoundary fallback={<SectionError />}>
  <DashboardWidget />
</ErrorBoundary>
```

---

## Common Patterns

### Custom data-fetching hook

```tsx
// hooks/useAsync.ts
interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

function useAsync<T>(asyncFn: () => Promise<T>, deps: React.DependencyList) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    asyncFn()
      .then(data => {
        if (!cancelled) setState({ data, isLoading: false, error: null });
      })
      .catch(error => {
        if (!cancelled) setState({ data: null, isLoading: false, error });
      });

    return () => { cancelled = true; };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return state;
}
```

### Compound components

```tsx
// Flexible API via compound components + context
const Tabs = ({ children, defaultTab }: TabsProps) => {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={styles.tabs}>{children}</div>
    </TabsContext.Provider>
  );
};

Tabs.List = function TabList({ children }) {
  return <div role="tablist">{children}</div>;
};

Tabs.Tab = function Tab({ id, children }) {
  const { activeTab, setActiveTab } = useContext(TabsContext);
  return (
    <button role="tab" aria-selected={activeTab === id} onClick={() => setActiveTab(id)}>
      {children}
    </button>
  );
};

Tabs.Panel = function TabPanel({ id, children }) {
  const { activeTab } = useContext(TabsContext);
  return activeTab === id ? <div role="tabpanel">{children}</div> : null;
};

// Usage
<Tabs defaultTab="overview">
  <Tabs.List>
    <Tabs.Tab id="overview">Overview</Tabs.Tab>
    <Tabs.Tab id="details">Details</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel id="overview"><Overview /></Tabs.Panel>
  <Tabs.Panel id="details"><Details /></Tabs.Panel>
</Tabs>
```

---

## Anti-Patterns

### ❌ Stale closures

```tsx
// ❌ Captures count from first render — always logs 0
useEffect(() => {
  const interval = setInterval(() => {
    console.log(count); // stale!
  }, 1000);
  return () => clearInterval(interval);
}, []); // count not in deps

// ✅ Use ref for values that shouldn't trigger re-runs
const countRef = useRef(count);
useEffect(() => { countRef.current = count; }, [count]);

useEffect(() => {
  const interval = setInterval(() => {
    console.log(countRef.current); // always fresh
  }, 1000);
  return () => clearInterval(interval);
}, []);
```

### ❌ Overusing useEffect for data transformation

```tsx
// ❌ Double render for no reason
const [sorted, setSorted] = useState([]);
useEffect(() => {
  setSorted([...items].sort((a, b) => a.name.localeCompare(b.name)));
}, [items]);

// ✅ Just derive it
const sorted = [...items].sort((a, b) => a.name.localeCompare(b.name));
// If expensive: const sorted = useMemo(() => [...items].sort(...), [items]);
```

### ❌ Key mutations during renders

```tsx
// ❌ Mutating state directly — React won't detect the change
const addItem = () => {
  items.push(newItem); // Mutation!
  setItems(items);     // Same reference — no re-render
};

// ✅ Always return new references
const addItem = () => setItems(prev => [...prev, newItem]);
const removeItem = (id: string) => setItems(prev => prev.filter(item => item.id !== id));
const updateItem = (id: string, updates: Partial<Item>) =>
  setItems(prev => prev.map(item => item.id === id ? { ...item, ...updates } : item));
```

---

## Tooling

### react-hooks ESLint plugin (already in base config)

```json
{
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "error"
  }
}
```

### React DevTools

Install the browser extension. Key features:
- **Profiler tab:** Record renders and identify which components re-render and why
- **Components tab:** Inspect props, state, and context in real time
- **Highlight updates:** Toggle "Highlight updates when components render" to spot excessive renders visually

---

## Customization

- **If using React Query/SWR:** Replace custom `useAsync` hook with the library's equivalent. The patterns for loading/error/data states are identical.
- **If using Zustand:** Replace Context + useReducer for global state. Keep component-local state in `useState`.
- **React Native:** Most hook patterns apply identically. Remove DOM-specific APIs (`document.addEventListener`, `IntersectionObserver`).

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
