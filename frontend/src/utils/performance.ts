import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private reportEndpoint = '/api/v1/analytics/performance';

  constructor() {
    this.initWebVitals();
    this.initCustomMetrics();
  }

  private initWebVitals() {
    getCLS(this.onMetric.bind(this));
    getFID(this.onMetric.bind(this));
    getFCP(this.onMetric.bind(this));
    getFCP(this.onMetric.bind(this));
    getLCP(this.onMetric.bind(this));
    getTTFB(this.onMetric.bind(this));
  }

  private initCustomMetrics() {
    // Track React component render times
    if (window.performance && window.performance.mark) {
      this.trackComponentPerformance();
    }

    // Track bundle load times
    this.trackBundleLoadTime();
  }

  private onMetric = (metric: any) => {
    const performanceMetric: PerformanceMetric = {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      timestamp: Date.now()
    };

    this.metrics.push(performanceMetric);
    this.reportMetric(performanceMetric);

    // Console log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`📊 ${metric.name}:`, metric.value, `(${metric.rating})`);
    }
  };

  private trackComponentPerformance() {
    // Track route changes
    const originalPushState = history.pushState;
    history.pushState = function(...args) {
      performance.mark('route-change-start');
      originalPushState.apply(history, args);

      setTimeout(() => {
        performance.mark('route-change-end');
        performance.measure('route-change', 'route-change-start', 'route-change-end');
      }, 0);
    };
  }

  private trackBundleLoadTime() {
    window.addEventListener('load', () => {
      const loadTime = performance.now();
      this.onMetric({
        name: 'bundle-load-time',
        value: loadTime,
        rating: loadTime < 3000 ? 'good' : loadTime < 5000 ? 'needs-improvement' : 'poor'
      });
    });
  }

  private async reportMetric(metric: PerformanceMetric) {
    try {
      await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(metric),
      });
    } catch (error) {
      console.warn('Failed to report performance metric:', error);
    }
  }

  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter(m => m.name === name);
  }
}

export const performanceMonitor = new PerformanceMonitor();

// React Performance HOC
export function withPerformanceTracking<T extends object>(
  Component: React.ComponentType<T>,
  componentName: string
) {
  return function PerformanceTrackedComponent(props: T) {
    React.useEffect(() => {
      const startMark = `${componentName}-render-start`;
      const endMark = `${componentName}-render-end`;
      const measureName = `${componentName}-render-time`;

      performance.mark(startMark);

      return () => {
        performance.mark(endMark);
        performance.measure(measureName, startMark, endMark);

        const measure = performance.getEntriesByName(measureName)[0];
        if (measure) {
          performanceMonitor['onMetric']({
            name: `component-${componentName}`,
            value: measure.duration,
            rating: measure.duration < 16 ? 'good' : measure.duration < 50 ? 'needs-improvement' : 'poor'
          });
        }
      };
    });

    return React.createElement(Component, props);
  };
}

// Bundle analyzer utility
export function analyzeBundleSize() {
  if (process.env.NODE_ENV === 'development') {
    import('webpack-bundle-analyzer').then(({ BundleAnalyzerPlugin }) => {
      console.log('📦 Bundle analysis available at http://localhost:8888');
    }).catch(() => {
      console.log('📦 Install webpack-bundle-analyzer for bundle analysis');
    });
  }
}

// Performance utilities
export const measurePerformance = (name: string, fn: () => void) => {
  const start = performance.now();
  fn();
  const end = performance.now();
  console.log(`${name} took ${end - start} milliseconds`);
};

export const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Web Vitals monitoring
export const reportWebVitals = (onPerfEntry?: (metric: any) => void) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

// React DevTools profiler
export const withProfiler = (Component: React.ComponentType<any>, id: string) => {
  if (process.env.NODE_ENV === 'development') {
    return React.memo(Component);
  }
  return Component;
};

// Performance observer for custom metrics
export const observePerformance = () => {
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        console.log(`Performance entry: ${entry.name} - ${entry.duration}ms`);
      });
    });
    observer.observe({ entryTypes: ['measure', 'navigation'] });
  }
};
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private isEnabled: boolean = true;

  constructor() {
    this.initWebVitals();
    this.initCustomMetrics();
  }

  private initWebVitals() {
    if (!this.isEnabled) return;

    getCLS(this.onVital);
    getFID(this.onVital);
    getFCP(this.onVital);
    getLCP(this.onVital);
    getTTFB(this.onVital);
  }

  private onVital = (metric: any) => {
    const performanceMetric: PerformanceMetric = {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      timestamp: Date.now()
    };

    this.metrics.push(performanceMetric);
    this.reportMetric(performanceMetric);
  };

  private initCustomMetrics() {
    // Track route changes
    this.measureRouteChange();
    
    // Track API response times
    this.measureAPIPerformance();
    
    // Track component render times
    this.measureComponentPerformance();
  }

  private measureRouteChange() {
    let routeStartTime = performance.now();
    
    window.addEventListener('beforeunload', () => {
      routeStartTime = performance.now();
    });

    window.addEventListener('load', () => {
      const routeTime = performance.now() - routeStartTime;
      this.addCustomMetric('route-change', routeTime);
    });
  }

  private measureAPIPerformance() {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const startTime = performance.now();
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.addCustomMetric('api-response', duration, {
          url: args[0] as string,
          status: response.status
        });
        
        return response;
      } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.addCustomMetric('api-error', duration, {
          url: args[0] as string,
          error: true
        });
        
        throw error;
      }
    };
  }

  private measureComponentPerformance() {
    // React Performance API integration
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'measure') {
            this.addCustomMetric('component-render', entry.duration, {
              component: entry.name
            });
          }
        });
      });
      
      observer.observe({ entryTypes: ['measure'] });
    }
  }

  private addCustomMetric(name: string, value: number, metadata?: any) {
    const rating = this.getRating(name, value);
    
    const metric: PerformanceMetric = {
      name,
      value,
      rating,
      timestamp: Date.now()
    };

    this.metrics.push(metric);
    this.reportMetric(metric, metadata);
  }

  private getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const thresholds: Record<string, [number, number]> = {
      'route-change': [1000, 2500],
      'api-response': [200, 1000],
      'component-render': [16, 50]
    };

    const [good, poor] = thresholds[name] || [100, 300];
    
    if (value <= good) return 'good';
    if (value <= poor) return 'needs-improvement';
    return 'poor';
  }

  private reportMetric(metric: PerformanceMetric, metadata?: any) {
    // Send to analytics endpoint
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/v1/analytics/performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric, metadata })
      }).catch(console.error);
    }

    // Development logging
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚀 Performance: ${metric.name}`);
      console.log(`Value: ${metric.value.toFixed(2)}ms`);
      console.log(`Rating: ${metric.rating}`);
      if (metadata) console.log('Metadata:', metadata);
      console.groupEnd();
    }
  }

  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter(m => m.name === name);
  }

  public getAverageMetric(name: string): number {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return 0;
    
    return metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length;
  }

  public generateReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      totalMetrics: this.metrics.length,
      vitals: {
        CLS: this.getAverageMetric('CLS'),
        FID: this.getAverageMetric('FID'),
        FCP: this.getAverageMetric('FCP'),
        LCP: this.getAverageMetric('LCP'),
        TTFB: this.getAverageMetric('TTFB')
      },
      custom: {
        routeChange: this.getAverageMetric('route-change'),
        apiResponse: this.getAverageMetric('api-response'),
        componentRender: this.getAverageMetric('component-render')
      }
    };

    return JSON.stringify(report, null, 2);
  }

  public disable() {
    this.isEnabled = false;
  }

  public enable() {
    this.isEnabled = true;
  }
}

export const performanceMonitor = new PerformanceMonitor();
export default performanceMonitor;
