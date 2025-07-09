
import os
import re
import ast
import json
import subprocess
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path
import streamlit as st
from logging_manager import log_warning, log_critical, LogCategory

class SecurityScanner:
    """Automated security scanning and vulnerability detection."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.scan_results = {}
        self.vulnerability_db = self._load_vulnerability_patterns()
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Load known vulnerability patterns."""
        return {
            'sql_injection': [
                r'\.execute\(.*\+.*[^?]\)',  # String concatenation in execute (not parameterized)
                r'\.execute\(.*format\([^?]',  # String formatting in execute
                r'\.execute\(.*%[^(]',  # Old-style string formatting
                r'cursor\.execute\([^"\']*["\'][^"\']*\+',  # Direct concatenation
            ],
            'xss_vulnerabilities': [
                r'st\.write\(.*\+.*[^)]\)',  # Unsafe concatenation in st.write
                r'st\.markdown\(.*\+.*unsafe_allow_html=True',  # Unsafe HTML
                r'st\.html\(.*\+',  # Any concatenation in st.html
                r'innerHTML\s*=.*\+',  # Direct innerHTML assignment
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'["\'][A-Za-z0-9]{32,}["\']',  # Long strings that might be secrets
            ],
            'unsafe_eval': [
                r'eval\(',
                r'exec\(',
                r'__import__\(',
                r'compile\(',
            ],
            'path_traversal': [
                r'open\(.*\+.*\)',
                r'os\.path\.join\(.*input',
                r'\.\./',
                r'\\\.\\.',
            ],
            'unsafe_pickle': [
                r'pickle\.loads\(',
                r'pickle\.load\(',
                r'cPickle\.loads\(',
            ]
        }
    
    def run_full_security_scan(self) -> Dict[str, Any]:
        """Run complete security scan."""
        scan_start = datetime.now()
        
        results = {
            'scan_timestamp': scan_start.isoformat(),
            'code_vulnerabilities': self.scan_code_vulnerabilities(),
            'dependency_vulnerabilities': self.scan_dependencies(),
            'database_security': self.scan_database_security(),
            'configuration_security': self.scan_configuration(),
            'file_permissions': self.scan_file_permissions(),
            'overall_risk_score': 0,
            'recommendations': []
        }
        
        # Calculate overall risk score
        results['overall_risk_score'] = self._calculate_risk_score(results)
        results['recommendations'] = self._generate_recommendations(results)
        
        # Log security scan results
        if results['overall_risk_score'] > 70:
            log_critical(
                f"High security risk detected: {results['overall_risk_score']}/100",
                details=results,
                category=LogCategory.SYSTEM_ERROR
            )
        elif results['overall_risk_score'] > 40:
            log_warning(
                f"Medium security risk detected: {results['overall_risk_score']}/100",
                details=results,
                category=LogCategory.SYSTEM_ERROR
            )
        
        return results
    
    def scan_code_vulnerabilities(self) -> Dict[str, List[Dict]]:
        """Scan code for security vulnerabilities."""
        vulnerabilities = {}
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "tests/" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_vulnerabilities = []
                
                # Check each vulnerability pattern
                for vuln_type, patterns in self.vulnerability_db.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            
                            file_vulnerabilities.append({
                                'type': vuln_type,
                                'pattern': pattern,
                                'line': line_num,
                                'code': match.group(0),
                                'severity': self._get_severity(vuln_type)
                            })
                
                if file_vulnerabilities:
                    vulnerabilities[str(file_path)] = file_vulnerabilities
                    
            except Exception as e:
                log_warning(f"Error scanning file {file_path}: {str(e)}", 
                          category=LogCategory.SYSTEM_ERROR)
        
        return vulnerabilities
    
    def scan_dependencies(self) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities."""
        try:
            # Run safety check if available
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                
                # Check for known vulnerable packages
                vulnerable_packages = []
                outdated_packages = []
                
                for package in packages:
                    name = package['name'].lower()
                    version = package['version']
                    
                    # Check against known vulnerable packages
                    if self._is_vulnerable_package(name, version):
                        vulnerable_packages.append({
                            'name': name,
                            'version': version,
                            'vulnerability': 'Known security issue'
                        })
                
                return {
                    'total_packages': len(packages),
                    'vulnerable_packages': vulnerable_packages,
                    'outdated_packages': outdated_packages,
                    'scan_successful': True
                }
            
        except Exception as e:
            log_warning(f"Dependency scan failed: {str(e)}", 
                       category=LogCategory.SYSTEM_ERROR)
        
        return {
            'scan_successful': False,
            'error': 'Could not scan dependencies'
        }
    
    def scan_database_security(self) -> Dict[str, Any]:
        """Scan database configuration for security issues."""
        issues = []
        
        db_path = self.project_root / "tradesense.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check for SQL injection vulnerabilities in stored procedures
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' OR type='trigger'")
                stored_code = cursor.fetchall()
                
                for code_row in stored_code:
                    if code_row[0]:
                        # Check for dynamic SQL construction
                        if any(pattern in code_row[0].lower() for pattern in ['||', 'concat', '+']):
                            issues.append({
                                'type': 'dynamic_sql',
                                'description': 'Potential SQL injection in stored code',
                                'severity': 'high'
                            })
                
                # Check for default passwords or weak configurations
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                if ('users',) in tables:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE password='default' OR password=''")
                    weak_passwords = cursor.fetchone()[0]
                    
                    if weak_passwords > 0:
                        issues.append({
                            'type': 'weak_passwords',
                            'description': f'{weak_passwords} users with default/empty passwords',
                            'severity': 'critical'
                        })
                
                conn.close()
                
            except Exception as e:
                issues.append({
                    'type': 'scan_error',
                    'description': f'Database scan failed: {str(e)}',
                    'severity': 'medium'
                })
        
        return {
            'issues': issues,
            'database_exists': db_path.exists()
        }
    
    def scan_configuration(self) -> Dict[str, Any]:
        """Scan configuration files for security issues."""
        issues = []
        
        config_files = [
            '.env', '.env.local', '.env.production',
            'config.py', 'settings.py',
            '.replit'
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for exposed secrets
                    for pattern in self.vulnerability_db['hardcoded_secrets']:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append({
                                'file': config_file,
                                'type': 'exposed_secret',
                                'description': 'Potential hardcoded secret found',
                                'severity': 'high'
                            })
                    
                    # Check for debug mode enabled
                    if re.search(r'debug\s*=\s*true', content, re.IGNORECASE):
                        issues.append({
                            'file': config_file,
                            'type': 'debug_enabled',
                            'description': 'Debug mode enabled in production',
                            'severity': 'medium'
                        })
                
                except Exception as e:
                    issues.append({
                        'file': config_file,
                        'type': 'scan_error',
                        'description': f'Could not scan config file: {str(e)}',
                        'severity': 'low'
                    })
        
        return {
            'issues': issues,
            'files_scanned': len([f for f in config_files if (self.project_root / f).exists()])
        }
    
    def scan_file_permissions(self) -> Dict[str, Any]:
        """Scan file permissions for security issues."""
        issues = []
        
        # Check for overly permissive files
        sensitive_files = [
            'tradesense.db',
            'logs/*.log',
            '*.key',
            '*.pem'
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Check if file is world-readable or writable
                    if int(mode[2]) > 0:  # Others have permissions
                        issues.append({
                            'file': str(file_path),
                            'type': 'overly_permissive',
                            'permissions': mode,
                            'description': 'File accessible by others',
                            'severity': 'medium'
                        })
                
                except Exception as e:
                    continue  # Skip files we can't read
        
        return {
            'issues': issues
        }
    
    def _is_vulnerable_package(self, name: str, version: str) -> bool:
        """Check if a package version has known vulnerabilities."""
        # Known vulnerable packages (simplified list)
        vulnerable_packages = {
            'django': ['<3.2.13', '<4.0.4'],
            'flask': ['<2.1.0'],
            'requests': ['<2.28.0'],
            'urllib3': ['<1.26.9'],
            'cryptography': ['<37.0.0'],
            'pyyaml': ['<6.0']
        }
        
        if name in vulnerable_packages:
            vulnerable_versions = vulnerable_packages[name]
            for vuln_version in vulnerable_versions:
                if vuln_version.startswith('<'):
                    # Simple version comparison (in production, use packaging.version)
                    threshold = vuln_version[1:]
                    if version < threshold:
                        return True
        
        return False
    
    def _get_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type."""
        severity_map = {
            'sql_injection': 'critical',
            'xss_vulnerabilities': 'high',
            'hardcoded_secrets': 'critical',
            'unsafe_eval': 'high',
            'path_traversal': 'high',
            'unsafe_pickle': 'critical'
        }
        return severity_map.get(vuln_type, 'medium')
    
    def _calculate_risk_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall security risk score (0-100)."""
        score = 0
        
        # Code vulnerabilities
        code_vulns = results.get('code_vulnerabilities', {})
        for file_vulns in code_vulns.values():
            for vuln in file_vulns:
                if vuln['severity'] == 'critical':
                    score += 25
                elif vuln['severity'] == 'high':
                    score += 15
                elif vuln['severity'] == 'medium':
                    score += 5
        
        # Dependency vulnerabilities
        dep_vulns = results.get('dependency_vulnerabilities', {})
        vulnerable_packages = dep_vulns.get('vulnerable_packages', [])
        score += len(vulnerable_packages) * 10
        
        # Database security issues
        db_issues = results.get('database_security', {}).get('issues', [])
        for issue in db_issues:
            if issue['severity'] == 'critical':
                score += 20
            elif issue['severity'] == 'high':
                score += 10
        
        # Configuration issues
        config_issues = results.get('configuration_security', {}).get('issues', [])
        for issue in config_issues:
            if issue['severity'] == 'high':
                score += 15
            elif issue['severity'] == 'medium':
                score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []
        
        # Check for high-priority issues
        code_vulns = results.get('code_vulnerabilities', {})
        if code_vulns:
            recommendations.append("🔥 CRITICAL: Fix code vulnerabilities immediately")
            recommendations.append("• Use parameterized queries to prevent SQL injection")
            recommendations.append("• Sanitize all user inputs before display")
            recommendations.append("• Remove hardcoded secrets and use environment variables")
        
        dep_vulns = results.get('dependency_vulnerabilities', {})
        if dep_vulns.get('vulnerable_packages'):
            recommendations.append("⚠️ HIGH: Update vulnerable dependencies")
            recommendations.append("• Run 'pip install --upgrade package_name' for each vulnerable package")
            recommendations.append("• Consider using 'pip-audit' for automated dependency scanning")
        
        db_issues = results.get('database_security', {}).get('issues', [])
        if db_issues:
            recommendations.append("🛡️ MEDIUM: Improve database security")
            recommendations.append("• Change default passwords")
            recommendations.append("• Use prepared statements")
            recommendations.append("• Enable database encryption")
        
        # General recommendations
        if results['overall_risk_score'] > 50:
            recommendations.extend([
                "📋 GENERAL: Implement security best practices",
                "• Set up automated security scanning in CI/CD",
                "• Conduct regular penetration testing",
                "• Train development team on secure coding practices",
                "• Implement security code reviews"
            ])
        
        return recommendations

def render_security_dashboard():
    """Render security dashboard in Streamlit."""
    st.header("🛡️ Security Dashboard")
    
    scanner = SecurityScanner()
    
    # Run security scan
    if st.button("🔍 Run Security Scan", type="primary"):
        with st.spinner("Running comprehensive security scan..."):
            results = scanner.run_full_security_scan()
            st.session_state.security_results = results
    
    # Display results if available
    if hasattr(st.session_state, 'security_results'):
        results = st.session_state.security_results
        
        # Overall risk score
        risk_score = results['overall_risk_score']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if risk_score >= 70:
                st.error(f"🚨 Risk Score: {risk_score}/100")
            elif risk_score >= 40:
                st.warning(f"⚠️ Risk Score: {risk_score}/100")
            else:
                st.success(f"✅ Risk Score: {risk_score}/100")
        
        with col2:
            code_issues = sum(len(vulns) for vulns in results.get('code_vulnerabilities', {}).values())
            st.metric("Code Issues", code_issues)
        
        with col3:
            dep_issues = len(results.get('dependency_vulnerabilities', {}).get('vulnerable_packages', []))
            st.metric("Vulnerable Dependencies", dep_issues)
        
        # Detailed results
        st.subheader("📊 Scan Results")
        
        # Code vulnerabilities
        code_vulns = results.get('code_vulnerabilities', {})
        if code_vulns:
            with st.expander(f"🔍 Code Vulnerabilities ({sum(len(v) for v in code_vulns.values())} issues)"):
                for file_path, vulns in code_vulns.items():
                    st.write(f"**{file_path}**")
                    for vuln in vulns:
                        severity_color = {"critical": "🔥", "high": "🚨", "medium": "⚠️", "low": "ℹ️"}
                        st.write(f"{severity_color.get(vuln['severity'], 'ℹ️')} Line {vuln['line']}: {vuln['type']}")
                        st.code(vuln['code'])
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            st.subheader("🎯 Security Recommendations")
            for rec in recommendations:
                if rec.startswith('🔥'):
                    st.error(rec)
                elif rec.startswith('⚠️'):
                    st.warning(rec)
                elif rec.startswith('•'):
                    st.write(f"  {rec}")
                else:
                    st.info(rec)
        
        # Export results
        if st.button("📥 Export Security Report"):
            report_json = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON Report",
                data=report_json,
                file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    render_security_dashboard()
