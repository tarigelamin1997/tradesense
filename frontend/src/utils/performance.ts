
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
