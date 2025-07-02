
import { performanceMonitor } from '../utils/performance';

describe('Performance Monitoring', () => {
  beforeEach(() => {
    performanceMonitor.enable();
  });

  afterEach(() => {
    performanceMonitor.disable();
  });

  test('should track custom metrics', () => {
    const initialMetrics = performanceMonitor.getMetrics();
    const initialCount = initialMetrics.length;

    // Simulate adding a custom metric
    (performanceMonitor as any).addCustomMetric('test-metric', 100);

    const updatedMetrics = performanceMonitor.getMetrics();
    expect(updatedMetrics.length).toBe(initialCount + 1);
  });

  test('should calculate average metrics correctly', () => {
    // Add test metrics
    (performanceMonitor as any).addCustomMetric('test-avg', 100);
    (performanceMonitor as any).addCustomMetric('test-avg', 200);
    (performanceMonitor as any).addCustomMetric('test-avg', 300);

    const average = performanceMonitor.getAverageMetric('test-avg');
    expect(average).toBe(200);
  });

  test('should generate performance report', () => {
    (performanceMonitor as any).addCustomMetric('test-report', 150);
    
    const report = performanceMonitor.generateReport();
    const parsed = JSON.parse(report);
    
    expect(parsed).toHaveProperty('timestamp');
    expect(parsed).toHaveProperty('vitals');
    expect(parsed).toHaveProperty('custom');
  });

  test('should rate performance correctly', () => {
    const getRating = (performanceMonitor as any).getRating;
    
    expect(getRating('api-response', 100)).toBe('good');
    expect(getRating('api-response', 500)).toBe('needs-improvement');
    expect(getRating('api-response', 1500)).toBe('poor');
  });
});
