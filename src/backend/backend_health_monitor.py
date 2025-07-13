#!/usr/bin/env python3
"""
TradeSense Backend Health Monitor
Continuously monitors backend health and generates alerts
"""

import psutil
import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import logging
import asyncio
import aiohttp
from sqlalchemy import create_engine, text
from collections import deque
import warnings

# Ignore SQLAlchemy warnings
warnings.filterwarnings("ignore", category=Warning)

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configuration
MONITOR_INTERVAL = 60  # seconds
HISTORY_SIZE = 60  # Keep 1 hour of history
API_BASE_URL = "http://localhost:8000"
LOG_FILE = "backend_health.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.metrics_history = {
            "cpu_usage": deque(maxlen=HISTORY_SIZE),
            "memory_usage": deque(maxlen=HISTORY_SIZE),
            "api_response_time": deque(maxlen=HISTORY_SIZE),
            "db_response_time": deque(maxlen=HISTORY_SIZE),
            "api_health": deque(maxlen=HISTORY_SIZE),
            "db_health": deque(maxlen=HISTORY_SIZE),
            "disk_usage": deque(maxlen=HISTORY_SIZE),
            "active_connections": deque(maxlen=HISTORY_SIZE),
        }
        self.alerts = []
        self.start_time = datetime.now()
        
        # Load configuration
        try:
            from core.config import settings
            self.db_url = settings.database_url
            self.is_postgres = "postgresql" in self.db_url
        except:
            self.db_url = "sqlite:///./tradesense.db"
            self.is_postgres = False
    
    def get_system_metrics(self) -> Dict:
        """Get system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_available_gb = disk.free / (1024 * 1024 * 1024)
            
            # Process information
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            process_cpu_percent = process.cpu_percent()
            
            # Network connections
            connections = len(process.connections())
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_mb": memory_available_mb,
                "disk_percent": disk_percent,
                "disk_available_gb": disk_available_gb,
                "process_memory_mb": process_memory_mb,
                "process_cpu_percent": process_cpu_percent,
                "active_connections": connections,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def check_api_health(self) -> Dict:
        """Check API health and response time"""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/health", timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time": response_time,
                            "data": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "response_time": response_time,
                            "error": f"Status code: {response.status}"
                        }
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "error": "Timeout"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def check_database_health(self) -> Dict:
        """Check database health and response time"""
        try:
            start_time = time.time()
            engine = create_engine(self.db_url)
            
            with engine.connect() as conn:
                # Simple query to test connection
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Get table count
                if self.is_postgres:
                    table_count_query = text("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                else:
                    table_count_query = text("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table'
                    """)
                
                result = conn.execute(table_count_query)
                table_count = result.scalar()
                
                # Get approximate row counts
                row_counts = {}
                if self.is_postgres:
                    tables = ['users', 'trades', 'portfolios']
                    for table in tables:
                        try:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            row_counts[table] = result.scalar()
                        except:
                            row_counts[table] = "N/A"
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "table_count": table_count,
                    "row_counts": row_counts,
                    "database_type": "PostgreSQL" if self.is_postgres else "SQLite"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def analyze_metrics(self, current_metrics: Dict) -> List[Dict]:
        """Analyze metrics and generate alerts"""
        alerts = []
        
        # CPU alert
        if current_metrics.get("cpu_percent", 0) > 80:
            alerts.append({
                "level": "WARNING",
                "message": f"High CPU usage: {current_metrics['cpu_percent']}%",
                "metric": "cpu_percent",
                "value": current_metrics["cpu_percent"]
            })
        
        # Memory alert
        if current_metrics.get("memory_percent", 0) > 85:
            alerts.append({
                "level": "WARNING",
                "message": f"High memory usage: {current_metrics['memory_percent']}%",
                "metric": "memory_percent",
                "value": current_metrics["memory_percent"]
            })
        
        # Disk alert
        if current_metrics.get("disk_percent", 0) > 90:
            alerts.append({
                "level": "CRITICAL",
                "message": f"Critical disk usage: {current_metrics['disk_percent']}%",
                "metric": "disk_percent",
                "value": current_metrics["disk_percent"]
            })
        
        # API response time alert
        if current_metrics.get("api_response_time", 0) > 1.0:
            alerts.append({
                "level": "WARNING",
                "message": f"Slow API response: {current_metrics['api_response_time']:.2f}s",
                "metric": "api_response_time",
                "value": current_metrics["api_response_time"]
            })
        
        # Database response time alert
        if current_metrics.get("db_response_time", 0) > 0.5:
            alerts.append({
                "level": "WARNING",
                "message": f"Slow database response: {current_metrics['db_response_time']:.2f}s",
                "metric": "db_response_time",
                "value": current_metrics["db_response_time"]
            })
        
        return alerts
    
    def update_history(self, metrics: Dict):
        """Update metrics history"""
        timestamp = datetime.now()
        
        self.metrics_history["cpu_usage"].append({
            "timestamp": timestamp,
            "value": metrics.get("cpu_percent", 0)
        })
        
        self.metrics_history["memory_usage"].append({
            "timestamp": timestamp,
            "value": metrics.get("memory_percent", 0)
        })
        
        self.metrics_history["disk_usage"].append({
            "timestamp": timestamp,
            "value": metrics.get("disk_percent", 0)
        })
        
        self.metrics_history["active_connections"].append({
            "timestamp": timestamp,
            "value": metrics.get("active_connections", 0)
        })
        
        if "api_health" in metrics:
            self.metrics_history["api_response_time"].append({
                "timestamp": timestamp,
                "value": metrics["api_health"].get("response_time", 0)
            })
            self.metrics_history["api_health"].append({
                "timestamp": timestamp,
                "value": 1 if metrics["api_health"]["status"] == "healthy" else 0
            })
        
        if "db_health" in metrics:
            self.metrics_history["db_response_time"].append({
                "timestamp": timestamp,
                "value": metrics["db_health"].get("response_time", 0)
            })
            self.metrics_history["db_health"].append({
                "timestamp": timestamp,
                "value": 1 if metrics["db_health"]["status"] == "healthy" else 0
            })
    
    def generate_report(self) -> Dict:
        """Generate comprehensive health report"""
        uptime = datetime.now() - self.start_time
        
        # Calculate averages
        def calc_average(history_key):
            if history_key in self.metrics_history and self.metrics_history[history_key]:
                values = [item["value"] for item in self.metrics_history[history_key]]
                return sum(values) / len(values)
            return 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime),
            "current_alerts": len(self.alerts),
            "metrics_summary": {
                "avg_cpu_usage": calc_average("cpu_usage"),
                "avg_memory_usage": calc_average("memory_usage"),
                "avg_api_response_time": calc_average("api_response_time"),
                "avg_db_response_time": calc_average("db_response_time"),
                "api_uptime_percent": calc_average("api_health") * 100,
                "db_uptime_percent": calc_average("db_health") * 100,
            },
            "alerts": self.alerts[-10:]  # Last 10 alerts
        }
        
        return report
    
    async def monitor_cycle(self):
        """Single monitoring cycle"""
        logger.info("Starting health check cycle...")
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        # Check API health
        api_health = await self.check_api_health()
        
        # Check database health
        db_health = self.check_database_health()
        
        # Combine metrics
        all_metrics = {
            **system_metrics,
            "api_health": api_health,
            "db_health": db_health,
            "api_response_time": api_health.get("response_time", 0),
            "db_response_time": db_health.get("response_time", 0)
        }
        
        # Update history
        self.update_history(all_metrics)
        
        # Analyze and generate alerts
        new_alerts = self.analyze_metrics(all_metrics)
        for alert in new_alerts:
            logger.warning(f"ALERT: {alert['message']}")
            self.alerts.append({
                **alert,
                "timestamp": datetime.now().isoformat()
            })
        
        # Log current status
        logger.info(f"System: CPU={system_metrics.get('cpu_percent', 0):.1f}%, "
                   f"Memory={system_metrics.get('memory_percent', 0):.1f}%, "
                   f"Disk={system_metrics.get('disk_percent', 0):.1f}%")
        logger.info(f"API: {api_health['status']} ({api_health.get('response_time', 0):.3f}s)")
        logger.info(f"Database: {db_health['status']} ({db_health.get('response_time', 0):.3f}s)")
        
        # Save report
        report = self.generate_report()
        with open("backend_health_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return all_metrics
    
    async def run(self):
        """Run continuous monitoring"""
        logger.info("Backend Health Monitor started")
        logger.info(f"Monitoring interval: {MONITOR_INTERVAL} seconds")
        logger.info(f"API URL: {API_BASE_URL}")
        logger.info(f"Database: {self.db_url}")
        
        while True:
            try:
                await self.monitor_cycle()
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor cycle error: {e}")
            
            await asyncio.sleep(MONITOR_INTERVAL)

def generate_html_dashboard():
    """Generate HTML dashboard from latest report"""
    try:
        with open("backend_health_report.json", "r") as f:
            report = json.load(f)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>TradeSense Backend Health Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background-color: #333; color: white; padding: 20px; border-radius: 5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .alert {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .alert-WARNING {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
        .alert-CRITICAL {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
        .status-healthy {{ color: #28a745; }}
        .status-unhealthy {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TradeSense Backend Health Dashboard</h1>
            <p>Last Updated: {report['timestamp']}</p>
            <p>Uptime: {report['uptime_human']}</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['avg_cpu_usage']:.1f}%</div>
                <div class="metric-label">Average CPU Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['avg_memory_usage']:.1f}%</div>
                <div class="metric-label">Average Memory Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['api_uptime_percent']:.1f}%</div>
                <div class="metric-label">API Uptime</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['db_uptime_percent']:.1f}%</div>
                <div class="metric-label">Database Uptime</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['avg_api_response_time']:.3f}s</div>
                <div class="metric-label">Avg API Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['metrics_summary']['avg_db_response_time']:.3f}s</div>
                <div class="metric-label">Avg DB Response Time</div>
            </div>
        </div>
        
        <h2>Recent Alerts ({report['current_alerts']})</h2>
        <div class="alerts">
"""
        
        for alert in report.get('alerts', []):
            html += f"""
            <div class="alert alert-{alert['level']}">
                <strong>{alert['level']}</strong>: {alert['message']} - {alert['timestamp']}
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        with open("backend_health_dashboard.html", "w") as f:
            f.write(html)
        
        logger.info("HTML dashboard generated: backend_health_dashboard.html")
    except Exception as e:
        logger.error(f"Error generating HTML dashboard: {e}")

async def main():
    """Main entry point"""
    monitor = HealthMonitor()
    
    # Generate initial report
    await monitor.monitor_cycle()
    generate_html_dashboard()
    
    # Run continuous monitoring
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Health monitor stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")