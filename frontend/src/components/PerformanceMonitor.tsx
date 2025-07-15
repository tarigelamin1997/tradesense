import React, { useEffect, useRef } from 'react';

interface PerformanceMonitorProps {
  children: React.ReactNode;
}

interface VitalMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ children }) => {
  const metricsRef = useRef<VitalMetric[]>([]);

  const logMetric = (metric: any) => {
    const vitalMetric: VitalMetric = {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      timestamp: Date.now(),
    };

    metricsRef.current.push(vitalMetric);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`📊 Web Vital: ${metric.name}`, {
        value: `${Math.round(metric.value)}ms`,
        rating: metric.rating,
        threshold: getThreshold(metric.name, metric.rating),
      });
    }

    // Send to analytics in production
    if (process.env.NODE_ENV === 'production') {
      // You can integrate with your analytics service here
      // Example: gtag('event', 'web_vital', { name: metric.name, value: metric.value });
    }
  };

  const getThreshold = (name: string, rating: string) => {
    const thresholds: Record<string, Record<string, string>> = {
      CLS: { good: '< 0.1', poor: '≥ 0.25' },
      FCP: { good: '< 1.8s', poor: '≥ 3.0s' },
      FID: { good: '< 100ms', poor: '≥ 300ms' },
      LCP: { good: '< 2.5s', poor: '≥ 4.0s' },
      TTFB: { good: '< 800ms', poor: '≥ 1800ms' },
    };
    return thresholds[name]?.[rating] || 'unknown';
  };

  useEffect(() => {
    // Dynamically import web-vitals to measure Core Web Vitals
    import('web-vitals').then(({ onCLS, onFCP, onINP, onLCP, onTTFB }) => {
      onCLS(logMetric);
      onFCP(logMetric);
      onINP(logMetric); // INP replaced FID in web-vitals v5
      onLCP(logMetric);
      onTTFB(logMetric);
    });

    // Monitor resource loading
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'navigation') {
          const navigation = entry as PerformanceNavigationTiming;
          console.log('🚀 Navigation Timing:', {
            domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart),
            loadComplete: Math.round(navigation.loadEventEnd - navigation.fetchStart),
            firstByte: Math.round(navigation.responseStart - navigation.fetchStart),
          });
        }
      });
    });

    observer.observe({ entryTypes: ['navigation'] });

    // Memory usage monitoring (if available)
    if ('memory' in performance) {
      const memoryInfo = (performance as any).memory;
      console.log('💾 Memory Usage:', {
        used: `${Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024)}MB`,
        total: `${Math.round(memoryInfo.totalJSHeapSize / 1024 / 1024)}MB`,
        limit: `${Math.round(memoryInfo.jsHeapSizeLimit / 1024 / 1024)}MB`,
      });
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  // Expose metrics to global for debugging
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      (window as any).getPerformanceMetrics = () => metricsRef.current;
    }
  }, []);

  return <>{children}</>;
};

export default PerformanceMonitor;