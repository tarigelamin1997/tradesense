
import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from logging_manager import log_info, log_warning, LogCategory
from notification_system import create_system_alert, NotificationType, NotificationPriority

class ComplianceStandard(Enum):
    SOC2 = "soc2"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOX = "sox"
    ISO27001 = "iso27001"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNDER_REVIEW = "under_review"

class ComplianceFramework:
    """Comprehensive compliance and regulatory framework."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.compliance_requirements = self._load_compliance_requirements()
        self._init_database()
    
    def _init_database(self):
        """Initialize compliance tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                standard TEXT NOT NULL,
                control_id TEXT NOT NULL,
                control_name TEXT NOT NULL,
                requirement_description TEXT,
                current_status TEXT NOT NULL,
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assessor_name TEXT,
                evidence_description TEXT,
                remediation_plan TEXT,
                target_completion_date DATE,
                last_review_date DATE,
                next_review_date DATE,
                risk_level TEXT,
                implementation_notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                evidence_type TEXT NOT NULL,
                evidence_description TEXT,
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (assessment_id) REFERENCES compliance_assessments (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_name TEXT NOT NULL,
                standard TEXT NOT NULL,
                auditor_name TEXT,
                auditor_company TEXT,
                audit_start_date DATE,
                audit_end_date DATE,
                audit_status TEXT NOT NULL,
                overall_rating TEXT,
                findings_count INTEGER DEFAULT 0,
                critical_findings INTEGER DEFAULT 0,
                high_findings INTEGER DEFAULT 0,
                medium_findings INTEGER DEFAULT 0,
                low_findings INTEGER DEFAULT 0,
                audit_report_path TEXT,
                certification_status TEXT,
                certification_expiry_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_compliance_requirements(self) -> Dict[str, List[Dict]]:
        """Load compliance requirements for different standards."""
        return {
            ComplianceStandard.SOC2.value: [
                {
                    "control_id": "CC1.1",
                    "name": "Entity demonstrates commitment to integrity and ethical values",
                    "description": "The entity demonstrates a commitment to integrity and ethical values through policies, communications, and monitoring.",
                    "category": "Control Environment"
                },
                {
                    "control_id": "CC2.1", 
                    "name": "Communication and information systems support achievement of objectives",
                    "description": "The entity obtains or generates and uses relevant, quality information to support the functioning of internal control.",
                    "category": "Communication and Information"
                },
                {
                    "control_id": "CC3.1",
                    "name": "Risk assessment process for achieving objectives",
                    "description": "The entity specifies objectives with sufficient clarity to enable the identification and assessment of risks.",
                    "category": "Risk Assessment"
                },
                {
                    "control_id": "CC6.1",
                    "name": "Logical and physical access controls",
                    "description": "The entity implements logical and physical access controls to protect against threats to achieve objectives.",
                    "category": "Logical and Physical Access Controls"
                }
            ],
            ComplianceStandard.GDPR.value: [
                {
                    "control_id": "ART6",
                    "name": "Lawfulness of processing",
                    "description": "Processing is lawful only if and to the extent that at least one legal basis applies.",
                    "category": "Lawfulness of Processing"
                },
                {
                    "control_id": "ART7",
                    "name": "Conditions for consent",
                    "description": "Where processing is based on consent, the controller must demonstrate that consent was given.",
                    "category": "Consent"
                },
                {
                    "control_id": "ART17",
                    "name": "Right to erasure",
                    "description": "Data subjects have the right to obtain erasure of personal data under certain circumstances.",
                    "category": "Data Subject Rights"
                },
                {
                    "control_id": "ART32",
                    "name": "Security of processing",
                    "description": "Appropriate technical and organizational measures must ensure security of processing.",
                    "category": "Security"
                }
            ],
            ComplianceStandard.ISO27001.value: [
                {
                    "control_id": "A.5.1.1",
                    "name": "Information security policies",
                    "description": "A set of policies for information security shall be defined and approved by management.",
                    "category": "Information Security Policies"
                },
                {
                    "control_id": "A.6.1.1",
                    "name": "Information security roles and responsibilities",
                    "description": "All information security responsibilities shall be defined and allocated.",
                    "category": "Organization of Information Security"
                },
                {
                    "control_id": "A.9.1.1",
                    "name": "Access control policy",
                    "description": "An access control policy shall be established and reviewed based on business requirements.",
                    "category": "Access Control"
                }
            ]
        }
    
    def assess_compliance_control(self, standard: str, control_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess a specific compliance control."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if assessment already exists
            cursor.execute('''
                SELECT id FROM compliance_assessments 
                WHERE standard = ? AND control_id = ?
            ''', (standard, control_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing assessment
                cursor.execute('''
                    UPDATE compliance_assessments 
                    SET current_status = ?, assessment_date = CURRENT_TIMESTAMP,
                        assessor_name = ?, evidence_description = ?,
                        remediation_plan = ?, target_completion_date = ?,
                        risk_level = ?, implementation_notes = ?
                    WHERE id = ?
                ''', (
                    assessment_data['status'],
                    assessment_data.get('assessor_name'),
                    assessment_data.get('evidence_description'),
                    assessment_data.get('remediation_plan'),
                    assessment_data.get('target_completion_date'),
                    assessment_data.get('risk_level'),
                    assessment_data.get('implementation_notes'),
                    existing[0]
                ))
                assessment_id = existing[0]
            else:
                # Create new assessment
                cursor.execute('''
                    INSERT INTO compliance_assessments (
                        standard, control_id, control_name, requirement_description,
                        current_status, assessor_name, evidence_description,
                        remediation_plan, target_completion_date, risk_level,
                        implementation_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    standard,
                    control_id,
                    assessment_data.get('control_name'),
                    assessment_data.get('requirement_description'),
                    assessment_data['status'],
                    assessment_data.get('assessor_name'),
                    assessment_data.get('evidence_description'),
                    assessment_data.get('remediation_plan'),
                    assessment_data.get('target_completion_date'),
                    assessment_data.get('risk_level'),
                    assessment_data.get('implementation_notes')
                ))
                assessment_id = cursor.lastrowid
            
            conn.commit()
            
            # Log compliance assessment
            log_info(
                f"Compliance assessment completed: {standard} {control_id}",
                details={
                    'standard': standard,
                    'control_id': control_id,
                    'status': assessment_data['status']
                },
                category=LogCategory.BUSINESS_LOGIC
            )
            
            # Alert on non-compliance
            if assessment_data['status'] in ['non_compliant', 'partially_compliant']:
                create_system_alert(
                    title=f"🚨 Compliance Issue: {standard} {control_id}",
                    message=f"Control {control_id} is {assessment_data['status']}",
                    notification_type=NotificationType.WARNING,
                    priority=NotificationPriority.HIGH
                )
            
            return {
                'success': True,
                'assessment_id': assessment_id
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def schedule_compliance_audit(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a compliance audit."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO compliance_audits (
                    audit_name, standard, auditor_name, auditor_company,
                    audit_start_date, audit_end_date, audit_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_data['audit_name'],
                audit_data['standard'],
                audit_data['auditor_name'],
                audit_data['auditor_company'],
                audit_data['audit_start_date'],
                audit_data['audit_end_date'],
                'scheduled'
            ))
            
            audit_id = cursor.lastrowid
            conn.commit()
            
            # Send notification
            create_system_alert(
                title=f"📅 Compliance Audit Scheduled",
                message=f"{audit_data['audit_name']} scheduled for {audit_data['audit_start_date']}",
                notification_type=NotificationType.INFO,
                priority=NotificationPriority.MEDIUM
            )
            
            return {
                'success': True,
                'audit_id': audit_id
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def get_compliance_status(self, standard: Optional[str] = None) -> Dict[str, Any]:
        """Get overall compliance status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Base query
        query = '''
            SELECT 
                standard,
                COUNT(*) as total_controls,
                COUNT(CASE WHEN current_status = 'compliant' THEN 1 END) as compliant_controls,
                COUNT(CASE WHEN current_status = 'non_compliant' THEN 1 END) as non_compliant_controls,
                COUNT(CASE WHEN current_status = 'partially_compliant' THEN 1 END) as partially_compliant_controls,
                COUNT(CASE WHEN current_status = 'under_review' THEN 1 END) as under_review_controls
            FROM compliance_assessments
        '''
        
        params = []
        if standard:
            query += ' WHERE standard = ?'
            params.append(standard)
        
        query += ' GROUP BY standard'
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Calculate compliance percentage for each standard
        for result in results:
            if result['total_controls'] > 0:
                result['compliance_percentage'] = (result['compliant_controls'] / result['total_controls']) * 100
            else:
                result['compliance_percentage'] = 0
        
        conn.close()
        return {'standards': results}
    
    def get_upcoming_compliance_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming compliance deadlines."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                standard, control_id, control_name, target_completion_date,
                current_status, risk_level
            FROM compliance_assessments 
            WHERE target_completion_date IS NOT NULL 
            AND target_completion_date <= date('now', '+{} days')
            AND current_status != 'compliant'
            ORDER BY target_completion_date ASC
        '''.format(days_ahead))
        
        columns = [desc[0] for desc in cursor.description]
        deadlines = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return deadlines
    
    def generate_compliance_report(self, standard: str) -> Dict[str, Any]:
        """Generate a comprehensive compliance report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all assessments for the standard
        cursor.execute('''
            SELECT * FROM compliance_assessments 
            WHERE standard = ?
            ORDER BY control_id
        ''', (standard,))
        
        columns = [desc[0] for desc in cursor.description]
        assessments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get audit history
        cursor.execute('''
            SELECT * FROM compliance_audits 
            WHERE standard = ?
            ORDER BY audit_start_date DESC
        ''', (standard,))
        
        audit_columns = [desc[0] for desc in cursor.description]
        audits = [dict(zip(audit_columns, row)) for row in cursor.fetchall()]
        
        # Calculate summary statistics
        total_controls = len(assessments)
        compliant_controls = len([a for a in assessments if a['current_status'] == 'compliant'])
        non_compliant_controls = len([a for a in assessments if a['current_status'] == 'non_compliant'])
        
        compliance_percentage = (compliant_controls / total_controls * 100) if total_controls > 0 else 0
        
        conn.close()
        
        return {
            'standard': standard,
            'report_date': datetime.now().isoformat(),
            'summary': {
                'total_controls': total_controls,
                'compliant_controls': compliant_controls,
                'non_compliant_controls': non_compliant_controls,
                'compliance_percentage': compliance_percentage
            },
            'assessments': assessments,
            'audit_history': audits
        }

def render_compliance_dashboard():
    """Render compliance dashboard."""
    st.header("📋 Compliance & Regulatory Dashboard")
    
    compliance_framework = ComplianceFramework()
    
    # Compliance overview
    st.subheader("🎯 Compliance Overview")
    
    status_data = compliance_framework.get_compliance_status()
    
    if status_data['standards']:
        for standard_data in status_data['standards']:
            with st.expander(f"📊 {standard_data['standard'].upper()} - {standard_data['compliance_percentage']:.1f}% Compliant"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Controls", standard_data['total_controls'])
                
                with col2:
                    st.metric("Compliant", standard_data['compliant_controls'])
                
                with col3:
                    st.metric("Non-Compliant", standard_data['non_compliant_controls'])
                
                with col4:
                    st.metric("Under Review", standard_data['under_review_controls'])
                
                # Progress bar
                st.progress(standard_data['compliance_percentage'] / 100)
    else:
        st.info("No compliance assessments found. Start by conducting your first assessment below.")
    
    # Upcoming deadlines
    st.subheader("⏰ Upcoming Compliance Deadlines")
    
    deadlines = compliance_framework.get_upcoming_compliance_deadlines()
    
    if deadlines:
        for deadline in deadlines:
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(deadline['risk_level'], "⚪")
            
            st.warning(f"{risk_color} **{deadline['standard']} {deadline['control_id']}** - Due: {deadline['target_completion_date']}")
            st.write(f"Status: {deadline['current_status']} | Control: {deadline['control_name']}")
    else:
        st.success("✅ No upcoming compliance deadlines")
    
    # Compliance assessment form
    st.subheader("📝 Conduct Compliance Assessment")
    
    with st.form("compliance_assessment"):
        col1, col2 = st.columns(2)
        
        with col1:
            standard = st.selectbox("Compliance Standard", 
                ["soc2", "gdpr", "iso27001", "pci_dss", "hipaa"])
            
            # Get controls for selected standard
            requirements = compliance_framework.compliance_requirements.get(standard, [])
            control_options = [f"{req['control_id']} - {req['name']}" for req in requirements]
            
            selected_control = st.selectbox("Control", control_options)
            control_id = selected_control.split(' - ')[0] if selected_control else ""
            
            status = st.selectbox("Assessment Status", 
                ["compliant", "non_compliant", "partially_compliant", "under_review", "not_applicable"])
            
            risk_level = st.selectbox("Risk Level", ["low", "medium", "high", "critical"])
        
        with col2:
            assessor_name = st.text_input("Assessor Name")
            target_date = st.date_input("Target Completion Date", 
                value=datetime.now() + timedelta(days=30))
            
            evidence_description = st.text_area("Evidence Description")
            remediation_plan = st.text_area("Remediation Plan (if needed)")
            implementation_notes = st.text_area("Implementation Notes")
        
        if st.form_submit_button("📊 Submit Assessment", type="primary"):
            if control_id and status:
                # Find the control details
                control_details = next((req for req in requirements if req['control_id'] == control_id), {})
                
                assessment_data = {
                    'status': status,
                    'assessor_name': assessor_name,
                    'evidence_description': evidence_description,
                    'remediation_plan': remediation_plan,
                    'target_completion_date': target_date.isoformat(),
                    'risk_level': risk_level,
                    'implementation_notes': implementation_notes,
                    'control_name': control_details.get('name', ''),
                    'requirement_description': control_details.get('description', '')
                }
                
                result = compliance_framework.assess_compliance_control(standard, control_id, assessment_data)
                
                if result['success']:
                    st.success(f"✅ Assessment completed for {standard.upper()} {control_id}")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result['error']}")
            else:
                st.error("Please select a control and status")
    
    # Schedule audit
    st.subheader("📅 Schedule Compliance Audit")
    
    with st.form("schedule_audit"):
        col1, col2 = st.columns(2)
        
        with col1:
            audit_name = st.text_input("Audit Name", placeholder="Annual SOC 2 Type II Audit")
            audit_standard = st.selectbox("Standard", ["soc2", "gdpr", "iso27001", "pci_dss"])
            auditor_name = st.text_input("Auditor Name")
        
        with col2:
            auditor_company = st.text_input("Auditor Company")
            start_date = st.date_input("Audit Start Date")
            end_date = st.date_input("Audit End Date")
        
        if st.form_submit_button("📋 Schedule Audit"):
            if all([audit_name, audit_standard, auditor_name, start_date]):
                audit_data = {
                    'audit_name': audit_name,
                    'standard': audit_standard,
                    'auditor_name': auditor_name,
                    'auditor_company': auditor_company,
                    'audit_start_date': start_date.isoformat(),
                    'audit_end_date': end_date.isoformat()
                }
                
                result = compliance_framework.schedule_compliance_audit(audit_data)
                
                if result['success']:
                    st.success(f"✅ Audit scheduled: {audit_name}")
                else:
                    st.error(f"❌ Error: {result['error']}")
            else:
                st.error("Please fill in all required fields")

if __name__ == "__main__":
    render_compliance_dashboard()
