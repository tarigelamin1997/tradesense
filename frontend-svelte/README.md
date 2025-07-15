# TradeSense SvelteKit Frontend

A modern, fast, and clean trading platform frontend built with SvelteKit.

## Features

- ⚡ **50-70% less code** than React
- 🚀 **Blazing fast performance** with no virtual DOM
- 📊 **TradingView Lightweight Charts** integration
- 🎨 **Clean, minimal UI** with custom CSS
- 🔄 **Simple state management** with Svelte stores
- 📱 **Fully responsive** design

## Why SvelteKit?

- **Simpler than React**: No hooks, no useEffect, no providers
- **Better performance**: Smaller bundles, faster runtime
- **Developer friendly**: Write less code, ship more features
- **Built-in features**: Routing, SSR, and more out of the box

## Project Structure

```
src/
├── routes/          # Pages (file-based routing)
│   ├── +page.svelte # Dashboard
│   └── trades/      # Trade Log
├── lib/
│   ├── components/  # Reusable components
│   ├── stores/      # State management
│   └── api/         # API integration
└── app.html        # HTML template
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

3. Open http://localhost:3001

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Type checking

## Key Differences from React

### State Management
```svelte
<!-- Svelte -->
<script>
  let count = 0;
  $: doubled = count * 2;
</script>

<button on:click={() => count++}>
  Count: {count}, Doubled: {doubled}
</button>
```

vs React:
```jsx
// React
const [count, setCount] = useState(0);
const doubled = useMemo(() => count * 2, [count]);

return (
  <button onClick={() => setCount(count + 1)}>
    Count: {count}, Doubled: {doubled}
  </button>
);
```

### Component Props
```svelte
<!-- Svelte -->
<script>
  export let title;
  export let value;
</script>

<h1>{title}: {value}</h1>
```

vs React:
```jsx
// React
function Component({ title, value }) {
  return <h1>{title}: {value}</h1>;
}
```

## Next Steps

1. Connect to FastAPI backend
2. Add authentication
3. Implement real-time updates
4. Add more chart types
5. Build journal and analytics features