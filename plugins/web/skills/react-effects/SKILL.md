---
name: react-effects
description: React useEffect anti-pattern detection and correction guide. Use this skill whenever writing, reviewing, or modifying any React component that contains useEffect, or when about to add a useEffect hook. Also trigger when you see patterns like "setState inside useEffect", "effect chains", "derived state in effect", or "notify parent in effect". Covers 12 specific scenarios where Effects are unnecessary or misused, with correct alternatives. Even if the useEffect looks reasonable at first glance, consult this skill to verify it's truly needed.
---

# React Effects: When You Do and Don't Need Them

Effects are an escape hatch to synchronize React components with **external systems** (browser APIs, network, third-party libraries). Most component logic does not need Effects. Before writing or keeping a `useEffect`, run through the scenarios below — there's likely a simpler, more performant alternative.

## The Two Questions

Before every `useEffect`, ask:

1. **Is this transforming data for rendering?** If yes, compute it during render instead.
2. **Is this handling a user event?** If yes, put it in an event handler instead.

If neither applies, you might actually need an Effect.

---

## Scenarios Where Effects Are Wrong

### 1. Derived State from Props or State

The most common mistake. If a value can be calculated from existing props or state, it's not state at all — it's a render-time computation.

**Why the Effect is harmful:** React renders once with stale values, commits to DOM, then the Effect fires a second setState triggering another full render cycle. The user briefly sees outdated UI.

```tsx
// WRONG: Redundant state + unnecessary Effect
const [firstName, setFirstName] = useState('Taylor');
const [lastName, setLastName] = useState('Swift');
const [fullName, setFullName] = useState('');
useEffect(() => {
  setFullName(firstName + ' ' + lastName);
}, [firstName, lastName]);

// RIGHT: Compute during render — zero extra renders, zero extra state
const [firstName, setFirstName] = useState('Taylor');
const [lastName, setLastName] = useState('Swift');
const fullName = firstName + ' ' + lastName;
```

**Detection pattern:** `useEffect` whose only job is calling `setSomeState(f(props, state))`.

### 2. Caching Expensive Computations

When the computation is genuinely expensive (>1ms in production profiling), use `useMemo` — not an Effect with state.

```tsx
// WRONG: Effect + state for caching
const [visibleTodos, setVisibleTodos] = useState([]);
useEffect(() => {
  setVisibleTodos(getFilteredTodos(todos, filter));
}, [todos, filter]);

// RIGHT (simple case): Just compute it
const visibleTodos = getFilteredTodos(todos, filter);

// RIGHT (expensive): useMemo skips recomputation when deps haven't changed
const visibleTodos = useMemo(
  () => getFilteredTodos(todos, filter),
  [todos, filter]
);
```

**When is it expensive?** Use `console.time`/`console.timeEnd` in production mode. If the logged time is consistently >=1ms, memoize. Dev mode timings are unreliable due to extra checks.

### 3. Resetting All State When a Prop Changes

When a prop like `userId` changes and you want to clear all component state (form fields, scroll position, etc.), don't reset each piece of state in an Effect — use React's `key` mechanism.

**Why the Effect is harmful:** The component renders once with stale state (old comment shown for new user), then the Effect clears it, causing a second render. Every nested component with state needs its own reset Effect — fragile and error-prone.

```tsx
// WRONG: Effect to reset state on prop change
function ProfilePage({ userId }) {
  const [comment, setComment] = useState('');
  useEffect(() => {
    setComment('');
  }, [userId]);
  return /* ... */;
}

// RIGHT: key tells React "this is a different component instance"
function ProfilePage({ userId }) {
  return <Profile userId={userId} key={userId} />;
}

function Profile({ userId }) {
  const [comment, setComment] = useState(''); // Auto-resets when key changes
  return /* ... */;
}
```

**Detection pattern:** `useEffect(() => { setX(initial); setY(initial); ... }, [someProp])` resetting multiple states.

### 4. Adjusting Some State When a Prop Changes

Sometimes you don't want to reset *all* state — just adjust one piece. The best approach is often to avoid the state entirely and derive the value.

```tsx
// WRONG: Effect to clear selection when items change
function List({ items }) {
  const [selection, setSelection] = useState(null);
  useEffect(() => {
    setSelection(null);
  }, [items]);
  return /* ... */;
}

// BETTER: Store the ID, derive the selected object
function List({ items }) {
  const [selectedId, setSelectedId] = useState(null);
  // If the selected item is still in the list, keep it; otherwise null
  const selection = items.find(item => item.id === selectedId) ?? null;
  return /* ... */;
}
```

If you truly must adjust state during render (rare), you can do so without an Effect, but this pattern should be a last resort:

```tsx
function List({ items }) {
  const [prevItems, setPrevItems] = useState(items);
  const [selection, setSelection] = useState(null);
  if (items !== prevItems) {
    setPrevItems(items);
    setSelection(null);
  }
}
```

### 5. Event-Specific Logic in Effects

If code should run **because the user did something** (clicked a button, submitted a form), it belongs in an event handler — not an Effect that reacts to state changes.

**Why the Effect is harmful:** The logic runs whenever the tracked state changes, including on page load, navigation, or other state restorations — not just in response to the user action.

```tsx
// WRONG: Shows notification whenever product.isInCart becomes true
// (including page refresh, back navigation, etc.)
function ProductPage({ product, addToCart }) {
  useEffect(() => {
    if (product.isInCart) {
      showNotification(`Added ${product.name} to cart!`);
    }
  }, [product]);

  function handleBuyClick() {
    addToCart(product);
  }
}

// RIGHT: Notification is a direct response to user action
function ProductPage({ product, addToCart }) {
  function buyProduct() {
    addToCart(product);
    showNotification(`Added ${product.name} to cart!`);
  }

  function handleBuyClick() {
    buyProduct();
  }

  function handleCheckoutClick() {
    buyProduct();
    navigateTo('/checkout');
  }
}
```

**Detection pattern:** `useEffect` that runs `showNotification`, `navigate`, `alert`, or other side effects triggered by `[someFlag]` that was set in an event handler.

### 6. POST Requests Triggered by User Actions

Sending data to a server in response to a user action (form submit, button click) belongs in the event handler. Only truly display-driven requests (like analytics page views) belong in Effects.

```tsx
// WRONG: Roundabout way to send form data
const [jsonToSubmit, setJsonToSubmit] = useState(null);
useEffect(() => {
  if (jsonToSubmit !== null) {
    post('/api/register', jsonToSubmit);
  }
}, [jsonToSubmit]);

function handleSubmit(e) {
  e.preventDefault();
  setJsonToSubmit({ firstName, lastName });
}

// RIGHT: Submit directly in the event handler
function handleSubmit(e) {
  e.preventDefault();
  post('/api/register', { firstName, lastName });
}

// This analytics Effect IS correct — it runs because the component displayed
useEffect(() => {
  post('/analytics/event', { eventName: 'visit_form' });
}, []);
```

### 7. Chains of Effects

Multiple Effects where each one sets state that triggers the next Effect. This creates a cascade of unnecessary renders and makes the logic hard to follow.

**Why the Effect chain is harmful:** Each setState in the chain triggers a separate render pass. If there are 4 Effects in the chain, the component renders 5 times instead of once. The logic is scattered across multiple Effects making it hard to trace.

```tsx
// WRONG: Chain of Effects triggering each other
useEffect(() => {
  if (card !== null && card.gold) {
    setGoldCardCount(c => c + 1);
  }
}, [card]);

useEffect(() => {
  if (goldCardCount > 3) {
    setRound(r => r + 1);
    setGoldCardCount(0);
  }
}, [goldCardCount]);

useEffect(() => {
  if (round > 5) {
    setIsGameOver(true);
  }
}, [round]);

// RIGHT: Derive what you can, compute the rest in the event handler
const isGameOver = round > 5; // Derived, not state

function handlePlaceCard(nextCard) {
  if (isGameOver) throw Error('Game already ended.');

  setCard(nextCard);
  if (nextCard.gold) {
    if (goldCardCount < 3) {
      setGoldCardCount(goldCardCount + 1);
    } else {
      setGoldCardCount(0);
      setRound(round + 1);
      if (round === 5) {
        alert('Good game!');
      }
    }
  }
}
```

**Detection pattern:** Multiple `useEffect` hooks where one sets state that appears in another's dependency array.

### 8. Application Initialization

Code that should run once per app load (not once per component mount), like checking auth tokens or loading config from localStorage.

```tsx
// WRONG: Runs twice in StrictMode development, may cause issues
function App() {
  useEffect(() => {
    loadDataFromLocalStorage();
    checkAuthToken();
  }, []);
}

// RIGHT (option A): Module-level guard
let didInit = false;

function App() {
  useEffect(() => {
    if (!didInit) {
      didInit = true;
      loadDataFromLocalStorage();
      checkAuthToken();
    }
  }, []);
}

// RIGHT (option B): Module-level execution (runs on import, once)
if (typeof window !== 'undefined') {
  checkAuthToken();
  loadDataFromLocalStorage();
}

function App() {
  // ...
}
```

### 9. Notifying Parent Components of State Changes

Using an Effect to call a parent's callback after local state changes creates an extra render cycle and makes the update order unpredictable.

```tsx
// WRONG: Effect to notify parent — renders twice
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);
  useEffect(() => {
    onChange(isOn);
  }, [isOn, onChange]);

  function handleClick() {
    setIsOn(!isOn);
  }
}

// RIGHT: Update child + notify parent in the same event
// React batches both setState calls into a single render
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);

  function updateToggle(nextIsOn) {
    setIsOn(nextIsOn);
    onChange(nextIsOn); // Parent updates in the same batch
  }

  function handleClick() {
    updateToggle(!isOn);
  }
}

// BEST: Fully controlled — no local state at all
function Toggle({ isOn, onChange }) {
  function handleClick() {
    onChange(!isOn);
  }
}
```

**Detection pattern:** `useEffect(() => { onSomething(localState); }, [localState, onSomething])`.

### 10. Passing Data Up to Parent

Child fetches data, then uses an Effect to push it up to the parent. This inverts React's data flow and makes bugs hard to trace.

```tsx
// WRONG: Child fetches, then pushes data to parent via Effect
function Parent() {
  const [data, setData] = useState(null);
  return <Child onFetched={setData} />;
}

function Child({ onFetched }) {
  const data = useSomeAPI();
  useEffect(() => {
    if (data) onFetched(data);
  }, [onFetched, data]);
}

// RIGHT: Parent owns the data fetching, passes data down
function Parent() {
  const data = useSomeAPI();
  return <Child data={data} />;
}
```

**Principle:** Data flows down in React. If a child needs data and the parent also needs it, the parent should fetch it and pass it down.

### 11. Subscribing to External Stores

Subscribing to browser APIs or external data sources that change outside React's control (e.g., `navigator.onLine`, browser history, third-party state libraries).

```tsx
// SUBOPTIMAL: Manual subscription in Effect
function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);
  useEffect(() => {
    function update() { setIsOnline(navigator.onLine); }
    update();
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);
  return isOnline;
}

// RIGHT: useSyncExternalStore — purpose-built for this
function subscribe(callback) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function useOnlineStatus() {
  return useSyncExternalStore(
    subscribe,
    () => navigator.onLine,      // Client snapshot
    () => true                    // Server snapshot
  );
}
```

### 12. Data Fetching

This is one case where an Effect is appropriate — you need to synchronize with the network. But you must handle race conditions with a cleanup flag.

```tsx
// CORRECT: Effect with ignore flag for race condition handling
useEffect(() => {
  let ignore = false;

  fetchResults(query, page).then(json => {
    if (!ignore) {
      setResults(json);
    }
  });

  return () => { ignore = true; };
}, [query, page]);
```

For production apps, prefer extracting data fetching into a custom hook or using a library like TanStack Query / SWR that handles caching, deduplication, and race conditions automatically.

---

## Quick Reference: Do I Need This Effect?

| What the Effect does | Alternative |
|---|---|
| Computes a value from props/state | Compute during render (or `useMemo` if expensive) |
| Resets all state when a prop changes | Add a `key` prop |
| Adjusts some state when a prop changes | Derive the value instead of storing it |
| Runs code when user clicks/submits | Move to event handler |
| Sends POST request from user action | Move to event handler |
| Sets state that triggers another Effect | Consolidate into one event handler |
| Initializes app once | Module-level code or `didInit` guard |
| Calls parent's `onChange` after local setState | Call `onChange` in the same event handler |
| Pushes data from child to parent | Lift data fetching to parent |
| Subscribes to external data source | Use `useSyncExternalStore` |
| Fetches data | Keep the Effect but add cleanup; prefer TanStack Query |

## Review Checklist

When reviewing or writing a `useEffect`, verify:

1. **Necessity:** Can this be a render-time computation, `useMemo`, or event handler instead?
2. **Cleanup:** Does the Effect clean up subscriptions, timers, or connections?
3. **Race conditions:** Does async work use an `ignore` flag or abort controller?
4. **Dependencies:** Are all reactive values listed? No `eslint-disable` for exhaustive-deps?
5. **No chains:** Does setting state in this Effect trigger another Effect? If so, consolidate.
6. **Not a lifecycle:** Is this genuinely about synchronizing with an external system, or is it disguised `componentDidMount`/`componentDidUpdate` thinking?
