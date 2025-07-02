
# Development Guide

## React DevTools Setup

### Browser Extension
1. Install React Developer Tools extension:
   - [Chrome Extension](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
   - [Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

### Standalone App (for development)
```bash
npm install -g react-devtools
react-devtools
```

### Profiling Performance
1. Open React DevTools
2. Switch to "Profiler" tab
3. Click "Record" button
4. Interact with your app
5. Stop recording to see performance insights

## Performance Monitoring

### React StrictMode
StrictMode is enabled in App.js to help identify:
- Components with unsafe lifecycles
- Legacy string ref API usage
- Deprecated findDOMNode usage
- Unexpected side effects

### Lazy Loading
All major routes are lazy-loaded:
- DashboardPage
- UploadPage  
- LoginPage
- RegisterPage

### Performance Tips
- Use React.memo for expensive components
- Optimize re-renders with useCallback and useMemo
- Monitor bundle size with `npm run build`
- Use React Profiler to identify bottlenecks

## Debugging

### Error Boundary
Global error boundary catches runtime errors and provides:
- User-friendly error UI
- Console logging in development
- Error reporting in production

### Network Debugging
- Check Network tab for API calls
- Use React Query DevTools for cache inspection
- Monitor state changes in Zustand DevTools
# TradeSense Frontend Development Guide

## Development Environment Setup

### Prerequisites
- Node.js 18+ 
- npm 8+
- React DevTools browser extension

### Quick Start
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

## React DevTools Setup

### Installation
1. **Chrome**: Install [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
2. **Firefox**: Install [React Developer Tools](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)
3. **Edge**: Install from Chrome Web Store (compatible)

### Usage in Development
- **Components Tab**: Inspect React component tree, props, and state
- **Profiler Tab**: Analyze component render performance
- **Redux DevTools**: Monitor Redux state changes (requires Redux DevTools extension)

### Performance Profiling
1. Open React DevTools → Profiler tab
2. Click record button (🔴)
3. Interact with the application
4. Stop recording to see flame graph
5. Analyze components with longest render times

### Debug Commands (Development Console)
```javascript
// Get current performance metrics
getPerformanceMetrics()

// Check Redux store state
window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__

// Measure component render time
console.time('ComponentRender')
// ... component interaction
console.timeEnd('ComponentRender')
```

## Performance Optimization Features

### Lazy Loading
- All feature pages are lazy-loaded with React.lazy()
- Suspense boundaries provide loading states
- Code splitting reduces initial bundle size

### React StrictMode
- Enabled in development to catch side effects
- Double-renders components to detect issues
- Warns about deprecated APIs

### Web Vitals Monitoring
- Automatic Core Web Vitals measurement
- Console logging in development
- Performance metrics collection

## Development Workflow

### Running Tests
```bash
npm test                 # Run all tests
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report
```

### Building for Production
```bash
npm run build           # Production build
npm run preview         # Preview production build
```

### Code Quality
```bash
npm run lint            # ESLint
npm run type-check      # TypeScript checks
npm run format          # Prettier formatting
```

## Browser Compatibility
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues
1. **Slow initial load**: Check lazy loading implementation
2. **Memory leaks**: Use React DevTools Profiler
3. **Hydration errors**: Check server/client rendering differences

### Performance Guidelines
- Keep components small and focused
- Use React.memo for expensive components
- Optimize re-renders with useMemo/useCallback
- Monitor bundle size with webpack analyzer
