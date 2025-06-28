
import React, { useEffect, useState } from 'react';
import { performanceMonitor } from '../utils/performance';

interface PerformanceData {
  CLS: number;
  FID: number;
  FCP: number;
  LCP: number;
  TTFB: number;
  routeChange: number;
  apiResponse: number;
  componentRender: number;
}

const PerformanceMonitor: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Update performance data every 5 seconds in development
    if (process.env.NODE_ENV === 'development') {
      const interval = setInterval(() => {
        const vitals = {
          CLS: performanceMonitor.getAverageMetric('CLS'),
          FID: performanceMonitor.getAverageMetric('FID'),
          FCP: performanceMonitor.getAverageMetric('FCP'),
          LCP: performanceMonitor.getAverageMetric('LCP'),
          TTFB: performanceMonitor.getAverageMetric('TTFB'),
          routeChange: performanceMonitor.getAverageMetric('route-change'),
          apiResponse: performanceMonitor.getAverageMetric('api-response'),
          componentRender: performanceMonitor.getAverageMetric('component-render')
        };
        setPerformanceData(vitals);
      }, 5000);

      return () => clearInterval(interval);
    }
  }, []);

  const getRatingColor = (value: number, type: string): string => {
    const thresholds: Record<string, [number, number]> = {
      CLS: [0.1, 0.25],
      FID: [100, 300],
      FCP: [1800, 3000],
      LCP: [2500, 4000],
      TTFB: [800, 1800],
      routeChange: [1000, 2500],
      apiResponse: [200, 1000],
      componentRender: [16, 50]
    };

    const [good, poor] = thresholds[type] || [100, 300];
    
    if (value <= good) return 'text-green-600';
    if (value <= poor) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatValue = (value: number, type: string): string => {
    if (type === 'CLS') return value.toFixed(3);
    return `${Math.round(value)}ms`;
  };

  if (process.env.NODE_ENV !== 'development' || !performanceData) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="bg-blue-600 text-white px-3 py-2 rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
      >
        📊 Performance
      </button>
      
      {isVisible && (
        <div className="absolute bottom-12 right-0 bg-white shadow-xl rounded-lg p-4 w-80 border">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-800">Performance Metrics</h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="border-b pb-2 mb-2">
              <h4 className="font-medium text-gray-700 mb-1">Web Vitals</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex justify-between">
                  <span>CLS:</span>
                  <span className={getRatingColor(performanceData.CLS, 'CLS')}>
                    {formatValue(performanceData.CLS, 'CLS')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>FID:</span>
                  <span className={getRatingColor(performanceData.FID, 'FID')}>
                    {formatValue(performanceData.FID, 'FID')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>FCP:</span>
                  <span className={getRatingColor(performanceData.FCP, 'FCP')}>
                    {formatValue(performanceData.FCP, 'FCP')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>LCP:</span>
                  <span className={getRatingColor(performanceData.LCP, 'LCP')}>
                    {formatValue(performanceData.LCP, 'LCP')}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Custom Metrics</h4>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span>Route Change:</span>
                  <span className={getRatingColor(performanceData.routeChange, 'routeChange')}>
                    {formatValue(performanceData.routeChange, 'routeChange')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>API Response:</span>
                  <span className={getRatingColor(performanceData.apiResponse, 'apiResponse')}>
                    {formatValue(performanceData.apiResponse, 'apiResponse')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Component Render:</span>
                  <span className={getRatingColor(performanceData.componentRender, 'componentRender')}>
                    {formatValue(performanceData.componentRender, 'componentRender')}
                  </span>
                </div>
              </div>
            </div>
            
            <button
              onClick={() => {
                const report = performanceMonitor.generateReport();
                console.log('Performance Report:', report);
                navigator.clipboard?.writeText(report);
              }}
              className="w-full mt-3 bg-gray-100 text-gray-700 py-2 px-3 rounded text-xs hover:bg-gray-200 transition-colors"
            >
              Copy Report to Clipboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMonitor;
