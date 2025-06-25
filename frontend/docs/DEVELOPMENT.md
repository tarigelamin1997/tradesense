
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
