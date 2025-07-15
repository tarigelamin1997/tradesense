import React, { Suspense } from 'react';

const ReactQueryDevtools = React.lazy(() =>
  import('@tanstack/react-query-devtools').then(module => ({
    default: (module as any).ReactQueryDevtools
  }))
);

// Redux DevTools are built into Redux Toolkit - no separate import needed

export const DevTools: React.FC = () => {
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Suspense fallback={null}>
      <ReactQueryDevtools />
      {/* Redux DevTools are automatically enabled in development */}
    </Suspense>
  );
};

// Performance monitoring component
export const PerformanceMonitor: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // Monitor render performance
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'measure') {
            console.log(`Performance: ${entry.name} took ${entry.duration}ms`);
          }
        }
      });

      observer.observe({ entryTypes: ['measure'] });

      return () => observer.disconnect();
    }
  }, []);

  return <>{children}</>;
};

// Lazy loading wrapper with suspense
export const LazyRoute: React.FC<{
  component: React.LazyExoticComponent<React.ComponentType<any>>;
  fallback?: React.ReactNode;
}> = ({ component: Component, fallback = <div>Loading...</div> }) => {
  return (
    <Suspense fallback={fallback}>
      <Component />
    </Suspense>
  );
};