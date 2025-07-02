
import { useEffect, useState } from 'react';
import { performanceMonitor } from '../utils/performance';

interface PerformanceHookReturn {
  metrics: any[];
  isMonitoring: boolean;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  generateReport: () => string;
}

export const usePerformance = (): PerformanceHookReturn => {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(true);

  useEffect(() => {
    if (isMonitoring) {
      const interval = setInterval(() => {
        setMetrics(performanceMonitor.getMetrics());
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isMonitoring]);

  const startMonitoring = () => {
    performanceMonitor.enable();
    setIsMonitoring(true);
  };

  const stopMonitoring = () => {
    performanceMonitor.disable();
    setIsMonitoring(false);
  };

  const generateReport = () => {
    return performanceMonitor.generateReport();
  };

  return {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    generateReport
  };
};
