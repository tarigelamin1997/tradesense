
#!/bin/bash

# TradeSense Production Monitoring Setup
# Real-time monitoring with alerts

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Setup monitoring directory
setup_monitoring() {
    log "Setting up monitoring infrastructure..."
    
    mkdir -p monitoring/alerts
    mkdir -p monitoring/metrics
    mkdir -p monitoring/logs
    
    # Create monitoring configuration
    cat > monitoring/config.json << EOF
{
  "monitoring": {
    "enabled": true,
    "interval": 30,
    "alerts": {
      "email_enabled": false,
      "slack_enabled": false,
      "thresholds": {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "response_time_ms": 5000,
        "error_rate_percent": 5
      }
    },
    "metrics": {
      "retention_days": 30,
      "export_format": "json"
    }
  }
}
EOF
    
    log "✅ Monitoring configuration created"
}

# Create real-time monitoring script
create_monitor() {
    cat > monitoring/real_time_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
TradeSense Real-time Monitoring System
"""
import json
import time
import psutil
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

class TradeSenseMonitor:
    def __init__(self):
        self.config_path = Path("monitoring/config.json")
        self.metrics_dir = Path("monitoring/metrics")
        self.alerts_dir = Path("monitoring/alerts")
        
        # Load configuration
        with open(self.config_path) as f:
            self.config = json.load(f)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_system_metrics(self):
        """Collect system performance metrics."""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': dict(psutil.net_io_counters()._asdict()),
            'process_count': len(psutil.pids())
        }
    
    def check_application_health(self):
        """Check application endpoints health."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {}
        }
        
        endpoints = [
            'http://localhost:8000/api/health',
            'http://localhost:8000/api/v1/trades',
            'http://localhost:3000'  # Frontend
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                health_status['endpoints'][endpoint] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'status_code': response.status_code,
                    'response_time_ms': response_time
                }
            except Exception as e:
                health_status['endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time_ms': None
                }
        
        return health_status
    
    def check_thresholds(self, metrics):
        """Check if metrics exceed alert thresholds."""
        alerts = []
        thresholds = self.config['monitoring']['alerts']['thresholds']
        
        if metrics['cpu_percent'] > thresholds['cpu_percent']:
            alerts.append({
                'level': 'warning',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics['memory_percent'] > thresholds['memory_percent']:
            alerts.append({
                'level': 'warning',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics['disk_percent'] > thresholds['disk_percent']:
            alerts.append({
                'level': 'critical',
                'message': f"High disk usage: {metrics['disk_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def save_metrics(self, metrics, health_status):
        """Save metrics to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save system metrics
        metrics_file = self.metrics_dir / f"system_metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save health status
        health_file = self.metrics_dir / f"health_status_{timestamp}.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
    
    def send_alerts(self, alerts):
        """Send alerts via configured channels."""
        if not alerts:
            return
        
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert['message']}")
            
            # Save alert to file
            alert_file = self.alerts_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, 'w') as f:
                json.dump(alert, f, indent=2)
    
    def cleanup_old_metrics(self):
        """Remove old metric files."""
        retention_days = self.config['monitoring']['metrics']['retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for metrics_file in self.metrics_dir.glob("*.json"):
            if metrics_file.stat().st_mtime < cutoff_date.timestamp():
                metrics_file.unlink()
                self.logger.info(f"Removed old metrics file: {metrics_file}")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        try:
            # Collect metrics
            system_metrics = self.collect_system_metrics()
            health_status = self.check_application_health()
            
            # Check for alerts
            alerts = self.check_thresholds(system_metrics)
            
            # Save data
            self.save_metrics(system_metrics, health_status)
            
            # Send alerts if any
            if alerts:
                self.send_alerts(alerts)
            
            # Cleanup old files
            self.cleanup_old_metrics()
            
            # Log status
            self.logger.info(f"Monitoring cycle completed - CPU: {system_metrics['cpu_percent']:.1f}%, "
                           f"Memory: {system_metrics['memory_percent']:.1f}%, "
                           f"Alerts: {len(alerts)}")
            
        except Exception as e:
            self.logger.error(f"Monitoring cycle failed: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring."""
        self.logger.info("Starting TradeSense monitoring system...")
        
        interval = self.config['monitoring']['interval']
        
        while True:
            self.run_monitoring_cycle()
            time.sleep(interval)

if __name__ == "__main__":
    monitor = TradeSenseMonitor()
    monitor.start_monitoring()
EOF
    
    chmod +x monitoring/real_time_monitor.py
    log "✅ Real-time monitor created"
}

# Create monitoring dashboard
create_dashboard() {
    cat > monitoring/dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
TradeSense Monitoring Dashboard
"""
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(
    page_title="TradeSense Monitoring",
    page_icon="📊",
    layout="wide"
)

def load_recent_metrics():
    """Load recent metrics from files."""
    metrics_dir = Path("monitoring/metrics")
    
    if not metrics_dir.exists():
        return pd.DataFrame(), pd.DataFrame()
    
    # Load system metrics
    system_files = list(metrics_dir.glob("system_metrics_*.json"))
    system_data = []
    
    for file in sorted(system_files)[-50:]:  # Last 50 entries
        try:
            with open(file) as f:
                data = json.load(f)
                system_data.append(data)
        except:
            continue
    
    # Load health status
    health_files = list(metrics_dir.glob("health_status_*.json"))
    health_data = []
    
    for file in sorted(health_files)[-50:]:  # Last 50 entries
        try:
            with open(file) as f:
                data = json.load(f)
                health_data.append(data)
        except:
            continue
    
    return pd.DataFrame(system_data), pd.DataFrame(health_data)

def load_recent_alerts():
    """Load recent alerts."""
    alerts_dir = Path("monitoring/alerts")
    
    if not alerts_dir.exists():
        return pd.DataFrame()
    
    alert_files = list(alerts_dir.glob("alert_*.json"))
    alert_data = []
    
    for file in sorted(alert_files)[-20:]:  # Last 20 alerts
        try:
            with open(file) as f:
                data = json.load(f)
                alert_data.append(data)
        except:
            continue
    
    return pd.DataFrame(alert_data)

def main():
    st.title("🚀 TradeSense System Monitoring")
    st.markdown("Real-time system performance and health monitoring")
    
    # Load data
    system_df, health_df = load_recent_metrics()
    alerts_df = load_recent_alerts()
    
    if system_df.empty:
        st.warning("No monitoring data available. Start the monitoring system first.")
        st.code("python monitoring/real_time_monitor.py")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    latest_metrics = system_df.iloc[-1] if not system_df.empty else {}
    
    with col1:
        cpu_percent = latest_metrics.get('cpu_percent', 0)
        st.metric(
            "CPU Usage", 
            f"{cpu_percent:.1f}%",
            delta=f"{cpu_percent - system_df.iloc[-2].get('cpu_percent', 0):.1f}%" if len(system_df) > 1 else None
        )
    
    with col2:
        memory_percent = latest_metrics.get('memory_percent', 0)
        st.metric(
            "Memory Usage", 
            f"{memory_percent:.1f}%",
            delta=f"{memory_percent - system_df.iloc[-2].get('memory_percent', 0):.1f}%" if len(system_df) > 1 else None
        )
    
    with col3:
        disk_percent = latest_metrics.get('disk_percent', 0)
        st.metric(
            "Disk Usage", 
            f"{disk_percent:.1f}%",
            delta=f"{disk_percent - system_df.iloc[-2].get('disk_percent', 0):.1f}%" if len(system_df) > 1 else None
        )
    
    with col4:
        process_count = latest_metrics.get('process_count', 0)
        st.metric(
            "Processes", 
            f"{process_count}",
            delta=f"{process_count - system_df.iloc[-2].get('process_count', 0)}" if len(system_df) > 1 else None
        )
    
    # Performance charts
    st.subheader("📈 Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not system_df.empty:
            fig = px.line(system_df, y=['cpu_percent', 'memory_percent'], 
                         title="CPU & Memory Usage Over Time")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not system_df.empty:
            fig = px.line(system_df, y='disk_percent', 
                         title="Disk Usage Over Time")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Alerts section
    st.subheader("🚨 Recent Alerts")
    
    if not alerts_df.empty:
        for _, alert in alerts_df.iterrows():
            level = alert.get('level', 'info')
            message = alert.get('message', 'Unknown alert')
            timestamp = alert.get('timestamp', 'Unknown time')
            
            if level == 'critical':
                st.error(f"🚨 {message} - {timestamp}")
            elif level == 'warning':
                st.warning(f"⚠️ {message} - {timestamp}")
            else:
                st.info(f"ℹ️ {message} - {timestamp}")
    else:
        st.success("No recent alerts - system running smoothly! ✅")
    
    # Health status
    st.subheader("🔍 Application Health")
    
    if not health_df.empty:
        latest_health = health_df.iloc[-1]
        endpoints = latest_health.get('endpoints', {})
        
        for endpoint, status in endpoints.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(endpoint)
            
            with col2:
                if status.get('status') == 'healthy':
                    st.success("✅ Healthy")
                elif status.get('status') == 'unhealthy':
                    st.warning("⚠️ Unhealthy")
                else:
                    st.error("❌ Error")
            
            with col3:
                response_time = status.get('response_time_ms')
                if response_time:
                    st.write(f"{response_time:.0f}ms")
                else:
                    st.write("N/A")

if __name__ == "__main__":
    main()
EOF
    
    log "✅ Monitoring dashboard created"
}

# Main setup
main() {
    log "🚀 Setting up TradeSense monitoring infrastructure..."
    
    setup_monitoring
    create_monitor
    create_dashboard
    
    log "✅ Monitoring setup completed!"
    log "📊 Start monitoring: python monitoring/real_time_monitor.py"
    log "🖥️ View dashboard: streamlit run monitoring/dashboard.py --server.port=5001"
}

main "$@"
