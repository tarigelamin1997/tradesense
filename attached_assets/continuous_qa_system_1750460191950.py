
import os
import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
import sqlite3
from pathlib import Path
import schedule
import threading
from logging_manager import log_info, log_warning, log_error, LogCategory
from security_scanner import SecurityScanner
from notification_system import create_system_alert, NotificationType, NotificationPriority

class ContinuousQASystem:
    """Automated continuous quality assurance system."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.db_path = "tradesense.db"
        self.running = False
        self._init_database()
        self._setup_schedules()
    
    def _init_database(self):
        """Initialize QA tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,
                tests_run INTEGER DEFAULT 0,
                tests_passed INTEGER DEFAULT 0,
                tests_failed INTEGER DEFAULT 0,
                coverage_percentage REAL,
                security_score INTEGER,
                performance_score INTEGER,
                results_json TEXT,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dependency_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_packages INTEGER,
                outdated_packages INTEGER,
                vulnerable_packages INTEGER,
                packages_json TEXT,
                recommendations TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE DEFAULT CURRENT_DATE,
                code_quality_score REAL,
                test_coverage REAL,
                security_score REAL,
                performance_score REAL,
                bug_count INTEGER DEFAULT 0,
                critical_issues INTEGER DEFAULT 0,
                technical_debt_hours REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_schedules(self):
        """Setup automated QA schedules."""
        # Daily full test suite
        schedule.every().day.at("02:00").do(self.run_full_test_suite)
        
        # Hourly quick tests
        schedule.every().hour.do(self.run_quick_tests)
        
        # Daily dependency check
        schedule.every().day.at("03:00").do(self.check_dependencies)
        
        # Weekly security scan
        schedule.every().monday.at("04:00").do(self.run_security_scan)
        
        # Daily performance check
        schedule.every().day.at("01:00").do(self.run_performance_tests)
    
    def start_continuous_qa(self):
        """Start the continuous QA system."""
        if not self.running:
            self.running = True
            
            def run_scheduler():
                while self.running:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            log_info("Continuous QA system started", category=LogCategory.SYSTEM_ERROR)
    
    def stop_continuous_qa(self):
        """Stop the continuous QA system."""
        self.running = False
        log_info("Continuous QA system stopped", category=LogCategory.SYSTEM_ERROR)
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        start_time = datetime.now()
        
        try:
            log_info("Starting full test suite", category=LogCategory.SYSTEM_ERROR)
            
            # Run pytest with coverage
            result = subprocess.run([
                'python', '-m', 'pytest', 
                '--cov=.', 
                '--cov-report=json:coverage.json',
                '--json-report', 
                '--json-report-file=test_results.json',
                '-v'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=600)
            
            # Parse results
            test_results = self._parse_test_results()
            coverage_data = self._parse_coverage_results()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Store results
            self._store_qa_run_results({
                'run_type': 'full_test_suite',
                'status': 'success' if result.returncode == 0 else 'failed',
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': duration,
                'tests_run': test_results.get('total', 0),
                'tests_passed': test_results.get('passed', 0),
                'tests_failed': test_results.get('failed', 0),
                'coverage_percentage': coverage_data.get('coverage', 0),
                'results_json': json.dumps({
                    'test_results': test_results,
                    'coverage': coverage_data,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }),
                'error_message': result.stderr if result.returncode != 0 else None
            })
            
            # Send alerts for failures
            if result.returncode != 0:
                create_system_alert(
                    title="🚨 Test Suite Failed",
                    message=f"Full test suite failed with {test_results.get('failed', 0)} failing tests",
                    notification_type=NotificationType.ERROR,
                    priority=NotificationPriority.HIGH
                )
            
            return {
                'success': result.returncode == 0,
                'tests_run': test_results.get('total', 0),
                'tests_passed': test_results.get('passed', 0),
                'tests_failed': test_results.get('failed', 0),
                'coverage': coverage_data.get('coverage', 0),
                'duration': duration
            }
            
        except subprocess.TimeoutExpired:
            self._store_qa_run_results({
                'run_type': 'full_test_suite',
                'status': 'timeout',
                'start_time': start_time,
                'end_time': datetime.now(),
                'error_message': 'Test suite timed out after 10 minutes'
            })
            
            create_system_alert(
                title="⏰ Test Suite Timeout",
                message="Full test suite timed out after 10 minutes",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH
            )
            
            return {'success': False, 'error': 'timeout'}
            
        except Exception as e:
            log_error(f"Test suite execution failed: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            return {'success': False, 'error': str(e)}
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick smoke tests."""
        start_time = datetime.now()
        
        try:
            # Run only fast tests
            result = subprocess.run([
                'python', '-m', 'pytest', 
                '-m', 'not slow',  # Exclude slow tests
                '--tb=short',
                '-q'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=120)
            
            test_results = self._parse_test_output(result.stdout)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self._store_qa_run_results({
                'run_type': 'quick_tests',
                'status': 'success' if result.returncode == 0 else 'failed',
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': duration,
                'tests_run': test_results.get('total', 0),
                'tests_passed': test_results.get('passed', 0),
                'tests_failed': test_results.get('failed', 0),
                'results_json': json.dumps({
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }),
                'error_message': result.stderr if result.returncode != 0 else None
            })
            
            return {
                'success': result.returncode == 0,
                'duration': duration,
                'tests_run': test_results.get('total', 0)
            }
            
        except Exception as e:
            log_error(f"Quick tests failed: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            return {'success': False, 'error': str(e)}
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check for outdated and vulnerable dependencies."""
        try:
            # Get all installed packages
            result = subprocess.run([
                'pip', 'list', '--format=json'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                
                # Check for outdated packages
                outdated_result = subprocess.run([
                    'pip', 'list', '--outdated', '--format=json'
                ], capture_output=True, text=True, timeout=120)
                
                outdated_packages = []
                if outdated_result.returncode == 0:
                    outdated_packages = json.loads(outdated_result.stdout)
                
                # Store results
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO dependency_checks (
                        total_packages, outdated_packages, packages_json, recommendations
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    len(packages),
                    len(outdated_packages),
                    json.dumps({
                        'installed': packages,
                        'outdated': outdated_packages
                    }),
                    json.dumps([f"Update {pkg['name']} from {pkg['version']} to {pkg['latest_version']}" 
                              for pkg in outdated_packages])
                ))
                
                conn.commit()
                conn.close()
                
                # Alert if many packages are outdated
                if len(outdated_packages) > 5:
                    create_system_alert(
                        title="📦 Many Outdated Dependencies",
                        message=f"{len(outdated_packages)} packages need updates",
                        notification_type=NotificationType.WARNING,
                        priority=NotificationPriority.MEDIUM
                    )
                
                return {
                    'success': True,
                    'total_packages': len(packages),
                    'outdated_packages': len(outdated_packages),
                    'outdated_list': outdated_packages
                }
            
        except Exception as e:
            log_error(f"Dependency check failed: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            return {'success': False, 'error': str(e)}
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run security vulnerability scan."""
        try:
            scanner = SecurityScanner(str(self.project_root))
            results = scanner.run_full_security_scan()
            
            # Update QA run with security score
            self._store_qa_run_results({
                'run_type': 'security_scan',
                'status': 'success',
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'security_score': 100 - results['overall_risk_score'],  # Invert risk to get score
                'results_json': json.dumps(results)
            })
            
            # Alert on high risk
            if results['overall_risk_score'] > 70:
                create_system_alert(
                    title="🛡️ High Security Risk Detected",
                    message=f"Security risk score: {results['overall_risk_score']}/100",
                    notification_type=NotificationType.ERROR,
                    priority=NotificationPriority.CRITICAL
                )
            
            return {
                'success': True,
                'risk_score': results['overall_risk_score'],
                'vulnerabilities_found': sum(len(vulns) for vulns in results.get('code_vulnerabilities', {}).values())
            }
            
        except Exception as e:
            log_error(f"Security scan failed: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            return {'success': False, 'error': str(e)}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and load tests."""
        try:
            # Simple performance test - measure import time
            import time
            
            start = time.time()
            import analytics
            import_time = time.time() - start
            
            # Test data processing performance
            import pandas as pd
            test_data = pd.DataFrame({
                'pnl': [100, -50, 200, -30] * 1000,
                'symbol': ['ES'] * 4000,
                'entry_time': ['2024-01-01'] * 4000,
                'exit_time': ['2024-01-01'] * 4000
            })
            
            start = time.time()
            stats = analytics.compute_basic_stats(test_data)
            processing_time = time.time() - start
            
            # Calculate performance score (lower is better)
            performance_score = max(0, 100 - (import_time * 10 + processing_time * 5))
            
            self._store_qa_run_results({
                'run_type': 'performance_tests',
                'status': 'success',
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'performance_score': performance_score,
                'results_json': json.dumps({
                    'import_time': import_time,
                    'processing_time': processing_time,
                    'performance_score': performance_score
                })
            })
            
            return {
                'success': True,
                'performance_score': performance_score,
                'import_time': import_time,
                'processing_time': processing_time
            }
            
        except Exception as e:
            log_error(f"Performance tests failed: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            return {'success': False, 'error': str(e)}
    
    def _parse_test_results(self) -> Dict[str, int]:
        """Parse test results from JSON report."""
        try:
            with open(self.project_root / 'test_results.json', 'r') as f:
                data = json.load(f)
            
            return {
                'total': data.get('summary', {}).get('total', 0),
                'passed': data.get('summary', {}).get('passed', 0),
                'failed': data.get('summary', {}).get('failed', 0),
                'skipped': data.get('summary', {}).get('skipped', 0)
            }
        except:
            return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    
    def _parse_coverage_results(self) -> Dict[str, float]:
        """Parse coverage results from JSON report."""
        try:
            with open(self.project_root / 'coverage.json', 'r') as f:
                data = json.load(f)
            
            return {
                'coverage': data.get('totals', {}).get('percent_covered', 0)
            }
        except:
            return {'coverage': 0}
    
    def _parse_test_output(self, output: str) -> Dict[str, int]:
        """Parse test output for quick results."""
        import re
        
        # Look for pytest output patterns
        pattern = r'(\d+) passed.*?(\d+) failed'
        match = re.search(pattern, output)
        
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2))
            return {
                'total': passed + failed,
                'passed': passed,
                'failed': failed
            }
        
        # Fallback pattern
        if 'passed' in output:
            return {'total': 1, 'passed': 1, 'failed': 0}
        elif 'failed' in output:
            return {'total': 1, 'passed': 0, 'failed': 1}
        
        return {'total': 0, 'passed': 0, 'failed': 0}
    
    def _store_qa_run_results(self, results: Dict[str, Any]):
        """Store QA run results in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qa_runs (
                run_type, status, start_time, end_time, duration_seconds,
                tests_run, tests_passed, tests_failed, coverage_percentage,
                security_score, performance_score, results_json, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            results.get('run_type'),
            results.get('status'),
            results.get('start_time'),
            results.get('end_time'),
            results.get('duration_seconds'),
            results.get('tests_run'),
            results.get('tests_passed'),
            results.get('tests_failed'),
            results.get('coverage_percentage'),
            results.get('security_score'),
            results.get('performance_score'),
            results.get('results_json'),
            results.get('error_message')
        ))
        
        conn.commit()
        conn.close()
    
    def get_qa_dashboard_data(self) -> Dict[str, Any]:
        """Get data for QA dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent QA runs
        cursor.execute('''
            SELECT * FROM qa_runs 
            ORDER BY start_time DESC 
            LIMIT 20
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        recent_runs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get QA trends
        cursor.execute('''
            SELECT 
                DATE(start_time) as date,
                AVG(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_rate,
                AVG(coverage_percentage) as avg_coverage,
                AVG(security_score) as avg_security,
                AVG(performance_score) as avg_performance
            FROM qa_runs 
            WHERE start_time > datetime('now', '-30 days')
            GROUP BY DATE(start_time)
            ORDER BY date DESC
        ''')
        
        trend_columns = [desc[0] for desc in cursor.description]
        trends = [dict(zip(trend_columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'recent_runs': recent_runs,
            'trends': trends
        }

def render_qa_dashboard():
    """Render the QA dashboard."""
    st.header("🔧 Continuous QA Dashboard")
    
    qa_system = ContinuousQASystem()
    
    # Control panel
    st.subheader("⚙️ QA Control Panel")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run Full Test Suite", type="primary"):
            with st.spinner("Running full test suite..."):
                results = qa_system.run_full_test_suite()
                if results['success']:
                    st.success(f"✅ Tests completed: {results['tests_passed']}/{results['tests_run']} passed")
                else:
                    st.error("❌ Test suite failed")
    
    with col2:
        if st.button("⚡ Run Quick Tests"):
            with st.spinner("Running quick tests..."):
                results = qa_system.run_quick_tests()
                if results['success']:
                    st.success(f"✅ Quick tests passed in {results['duration']:.1f}s")
                else:
                    st.error("❌ Quick tests failed")
    
    with col3:
        if st.button("🔍 Security Scan"):
            with st.spinner("Running security scan..."):
                results = qa_system.run_security_scan()
                if results['success']:
                    st.success(f"✅ Security scan completed. Risk: {results['risk_score']}/100")
                else:
                    st.error("❌ Security scan failed")
    
    # Dashboard data
    dashboard_data = qa_system.get_qa_dashboard_data()
    
    # Recent runs
    st.subheader("📊 Recent QA Runs")
    
    if dashboard_data['recent_runs']:
        for run in dashboard_data['recent_runs'][:5]:
            with st.expander(f"{run['run_type']} - {run['status']} ({run['start_time']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Tests Run", run['tests_run'] or 0)
                    st.metric("Tests Passed", run['tests_passed'] or 0)
                
                with col2:
                    st.metric("Coverage", f"{run['coverage_percentage'] or 0:.1f}%")
                    st.metric("Duration", f"{run['duration_seconds'] or 0:.1f}s")
                
                with col3:
                    if run['security_score']:
                        st.metric("Security Score", f"{run['security_score']}/100")
                    if run['performance_score']:
                        st.metric("Performance Score", f"{run['performance_score']}/100")
                
                if run['error_message']:
                    st.error(f"Error: {run['error_message']}")
    
    # QA trends
    if dashboard_data['trends']:
        st.subheader("📈 QA Trends (Last 30 Days)")
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Success Rate', 'Test Coverage', 'Security Score', 'Performance Score')
        )
        
        dates = [trend['date'] for trend in dashboard_data['trends']]
        
        fig.add_trace(go.Scatter(
            x=dates, y=[trend['success_rate'] * 100 for trend in dashboard_data['trends']],
            name='Success Rate', line=dict(color='green')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=dates, y=[trend['avg_coverage'] or 0 for trend in dashboard_data['trends']],
            name='Coverage', line=dict(color='blue')
        ), row=1, col=2)
        
        fig.add_trace(go.Scatter(
            x=dates, y=[trend['avg_security'] or 0 for trend in dashboard_data['trends']],
            name='Security', line=dict(color='orange')
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=dates, y=[trend['avg_performance'] or 0 for trend in dashboard_data['trends']],
            name='Performance', line=dict(color='purple')
        ), row=2, col=2)
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_qa_dashboard()
