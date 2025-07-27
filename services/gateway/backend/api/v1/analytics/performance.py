
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import json

router = APIRouter()

class PerformanceMetric(BaseModel):
    name: str
    value: float
    rating: str
    timestamp: int

class PerformanceReport(BaseModel):
    metric: PerformanceMetric
    metadata: Optional[Dict[str, Any]] = None

class PerformanceAnalytics:
    def __init__(self):
        self.metrics_store = []
    
    def store_metric(self, report: PerformanceReport):
        """Store performance metric for analysis"""
        self.metrics_store.append({
            'metric': report.metric.dict(),
            'metadata': report.metadata,
            'received_at': datetime.utcnow().isoformat()
        })
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(self.metrics_store) > 1000:
            self.metrics_store = self.metrics_store[-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        if not self.metrics_store:
            return {'message': 'No performance data available'}
        
        # Group metrics by name
        metrics_by_name = {}
        for entry in self.metrics_store:
            metric = entry['metric']
            name = metric['name']
            
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            
            metrics_by_name[name].append(metric['value'])
        
        # Calculate averages and ratings
        summary = {}
        for name, values in metrics_by_name.items():
            avg_value = sum(values) / len(values)
            summary[name] = {
                'average': round(avg_value, 2),
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'rating': self._get_rating(name, avg_value)
            }
        
        return {
            'summary': summary,
            'total_metrics': len(self.metrics_store),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_rating(self, name: str, value: float) -> str:
        """Get performance rating based on metric name and value"""
        thresholds = {
            'CLS': (0.1, 0.25),
            'FID': (100, 300),
            'FCP': (1800, 3000),
            'LCP': (2500, 4000),
            'TTFB': (800, 1800),
            'route-change': (1000, 2500),
            'api-response': (200, 1000),
            'component-render': (16, 50)
        }
        
        good, poor = thresholds.get(name, (100, 300))
        
        if value <= good:
            return 'good'
        elif value <= poor:
            return 'needs-improvement'
        else:
            return 'poor'

# Global analytics instance
performance_analytics = PerformanceAnalytics()

@router.post("/performance")
async def record_performance_metric(report: PerformanceReport):
    """Record a performance metric"""
    try:
        performance_analytics.store_metric(report)
        return {"status": "success", "message": "Metric recorded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to record metric: {str(e)}")

@router.get("/performance/summary")
async def get_performance_summary():
    """Get performance analytics summary"""
    try:
        return performance_analytics.get_performance_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.get("/performance/vitals")
async def get_web_vitals():
    """Get Web Vitals specific metrics"""
    try:
        summary = performance_analytics.get_performance_summary()
        
        if 'summary' not in summary:
            return {'message': 'No vitals data available'}
        
        vitals = {}
        vital_names = ['CLS', 'FID', 'FCP', 'LCP', 'TTFB']
        
        for vital in vital_names:
            if vital in summary['summary']:
                vitals[vital] = summary['summary'][vital]
        
        return {
            'vitals': vitals,
            'generated_at': summary.get('generated_at')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vitals: {str(e)}")
