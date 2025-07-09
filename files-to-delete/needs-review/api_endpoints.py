
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from typing import Dict, List
from bulk_provisioning import BulkProvisioningManager
from auth import AuthManager

app = Flask(__name__)
CORS(app)

def authenticate_partner_api(request) -> str:
    """Authenticate partner API request and return partner_id."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    api_key = auth_header.split(' ')[1]
    
    # Validate API key and get partner_id
    auth_manager = AuthManager()
    # Implementation would check API key against database
    # For now, return demo partner
    return "demo_partner" if api_key.startswith('ts_') else None

@app.route('/api/v1/partner/bulk-provision', methods=['POST'])
def bulk_provision_accounts():
    """API endpoint for bulk account provisioning."""
    partner_id = authenticate_partner_api(request)
    if not partner_id:
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        data = request.get_json()
        
        job_name = data.get('job_name', 'API Bulk Import')
        accounts_data = data.get('accounts', [])
        settings = data.get('settings', {})
        
        # Validate required fields
        if not accounts_data:
            return jsonify({'error': 'No accounts provided'}), 400
        
        for account in accounts_data:
            if 'email' not in account:
                return jsonify({'error': 'Email required for all accounts'}), 400
        
        # Create bulk job
        bulk_manager = BulkProvisioningManager()
        result = bulk_manager.create_bulk_job(
            partner_id=partner_id,
            job_name=job_name,
            accounts_data=accounts_data,
            created_by='api'
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'job_id': result['job_id'],
                'total_accounts': len(accounts_data),
                'successful_accounts': result['successful'],
                'failed_accounts': result['failed'],
                'credentials_download_url': f'/api/v1/partner/jobs/{result["job_id"]}/credentials'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/partner/jobs/<int:job_id>/credentials', methods=['GET'])
def download_job_credentials(job_id: int):
    """Download credentials for a completed job."""
    partner_id = authenticate_partner_api(request)
    if not partner_id:
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        bulk_manager = BulkProvisioningManager()
        csv_data = bulk_manager.export_credentials(job_id)
        
        if csv_data:
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=credentials_{job_id}.csv'
            }
        else:
            return jsonify({'error': 'Job not found or no credentials available'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/partner/jobs/<int:job_id>/status', methods=['GET'])
def get_job_status(job_id: int):
    """Get status of a bulk provisioning job."""
    partner_id = authenticate_partner_api(request)
    if not partner_id:
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        bulk_manager = BulkProvisioningManager()
        job_status = bulk_manager.get_job_status(job_id)
        
        if job_status:
            return jsonify(job_status)
        else:
            return jsonify({'error': 'Job not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/partner/jobs', methods=['GET'])
def list_bulk_jobs():
    """List all bulk provisioning jobs for partner."""
    partner_id = authenticate_partner_api(request)
    if not partner_id:
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('tradesense.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, job_name, total_accounts, successful_accounts, 
                   failed_accounts, status, created_at, completed_at
            FROM bulk_provisioning_jobs 
            WHERE partner_id = ?
            ORDER BY created_at DESC
        ''', (partner_id,))
        
        jobs = cursor.fetchall()
        conn.close()
        
        job_list = []
        for job in jobs:
            job_list.append({
                'job_id': job[0],
                'job_name': job[1],
                'total_accounts': job[2],
                'successful_accounts': job[3],
                'failed_accounts': job[4],
                'status': job[5],
                'created_at': job[6],
                'completed_at': job[7]
            })
        
        return jsonify({'jobs': job_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
