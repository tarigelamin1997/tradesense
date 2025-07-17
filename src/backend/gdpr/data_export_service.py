"""
GDPR-compliant data export service for TradeSense.
Provides comprehensive user data export and deletion capabilities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import csv
import io
import zipfile
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.email_service import email_service
from core.config import settings


class DataExportService:
    """Manages GDPR-compliant data exports and deletions."""
    
    def __init__(self):
        self.export_tables = [
            # Core user data
            {
                "name": "user_profile",
                "query": """
                    SELECT 
                        id, email, full_name, created_at, last_login,
                        subscription_tier, subscription_status,
                        email_verified, phone_number,
                        metadata, settings
                    FROM users
                    WHERE id = :user_id
                """,
                "format": "json"
            },
            # Trading data
            {
                "name": "trades",
                "query": """
                    SELECT 
                        id, symbol, entry_date, exit_date, entry_price, exit_price,
                        quantity, trade_type, profit_loss, commission, notes,
                        tags, strategy, created_at, updated_at
                    FROM trades
                    WHERE user_id = :user_id
                    ORDER BY entry_date DESC
                """,
                "format": "csv"
            },
            # Journal entries
            {
                "name": "journal_entries",
                "query": """
                    SELECT 
                        id, title, content, mood, tags,
                        created_at, updated_at
                    FROM journal_entries
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """,
                "format": "json"
            },
            # Analytics events
            {
                "name": "analytics_events",
                "query": """
                    SELECT 
                        event_type, properties, created_at
                    FROM analytics_events
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 10000
                """,
                "format": "json"
            },
            # Support tickets
            {
                "name": "support_tickets",
                "query": """
                    SELECT 
                        t.id, t.subject, t.description, t.category,
                        t.priority, t.status, t.created_at, t.resolved_at,
                        array_agg(
                            json_build_object(
                                'message', m.message,
                                'created_at', m.created_at,
                                'is_internal', m.is_internal
                            ) ORDER BY m.created_at
                        ) as messages
                    FROM support_tickets t
                    LEFT JOIN support_ticket_messages m ON t.id = m.ticket_id
                    WHERE t.user_id = :user_id
                    GROUP BY t.id
                    ORDER BY t.created_at DESC
                """,
                "format": "json"
            },
            # Payments
            {
                "name": "payment_history",
                "query": """
                    SELECT 
                        id, amount, currency, status, description,
                        created_at
                    FROM payments
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """,
                "format": "csv"
            },
            # Feature flag evaluations
            {
                "name": "feature_flags",
                "query": """
                    SELECT DISTINCT ON (flag_key)
                        flag_key, value, evaluated_at
                    FROM feature_flag_evaluations
                    WHERE user_id = :user_id
                    ORDER BY flag_key, evaluated_at DESC
                """,
                "format": "json"
            },
            # User preferences
            {
                "name": "notification_preferences",
                "query": """
                    SELECT 
                        channel, enabled, categories,
                        created_at, updated_at
                    FROM notification_preferences
                    WHERE user_id = :user_id
                """,
                "format": "json"
            }
        ]
        
        self.deletion_tables = [
            # Order matters for foreign key constraints
            "feature_flag_evaluations",
            "notification_preferences",
            "support_ticket_messages",
            "support_tickets",
            "payments",
            "analytics_events",
            "journal_entries",
            "trades",
            "user_onboarding",
            "user_sessions",
            "users"
        ]
    
    async def create_export_request(
        self,
        user: User,
        request_type: str,  # 'export' or 'deletion'
        db: AsyncSession
    ) -> str:
        """Create a new data export or deletion request."""
        
        request_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO gdpr_requests (
                    id, user_id, request_type, status,
                    requested_at, expires_at
                ) VALUES (
                    :id, :user_id, :request_type, 'pending',
                    NOW(), NOW() + INTERVAL '30 days'
                )
            """),
            {
                "id": request_id,
                "user_id": user.id,
                "request_type": request_type
            }
        )
        
        await db.commit()
        
        # Send confirmation email
        await self._send_request_confirmation(user, request_type, request_id)
        
        # Process request asynchronously
        asyncio.create_task(self._process_request(request_id, user, request_type, db))
        
        return request_id
    
    async def get_request_status(
        self,
        request_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get status of a GDPR request."""
        
        result = await db.execute(
            text("""
                SELECT 
                    id, request_type, status,
                    requested_at, completed_at, expires_at,
                    download_url, error_message
                FROM gdpr_requests
                WHERE id = :request_id AND user_id = :user_id
            """),
            {
                "request_id": request_id,
                "user_id": user_id
            }
        )
        
        request = result.first()
        if not request:
            return None
        
        return {
            "id": str(request.id),
            "type": request.request_type,
            "status": request.status,
            "requested_at": request.requested_at,
            "completed_at": request.completed_at,
            "expires_at": request.expires_at,
            "download_url": request.download_url,
            "error": request.error_message
        }
    
    async def download_export(
        self,
        request_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[bytes]:
        """Download completed export data."""
        
        # Verify request
        result = await db.execute(
            text("""
                SELECT file_path, expires_at
                FROM gdpr_requests
                WHERE id = :request_id 
                AND user_id = :user_id
                AND request_type = 'export'
                AND status = 'completed'
            """),
            {
                "request_id": request_id,
                "user_id": user_id
            }
        )
        
        request = result.first()
        if not request:
            return None
        
        # Check expiration
        if request.expires_at < datetime.utcnow():
            return None
        
        # Read file
        try:
            with open(request.file_path, 'rb') as f:
                return f.read()
        except:
            return None
    
    async def _process_request(
        self,
        request_id: str,
        user: User,
        request_type: str,
        db: AsyncSession
    ):
        """Process GDPR request asynchronously."""
        
        try:
            if request_type == "export":
                await self._process_export(request_id, user, db)
            elif request_type == "deletion":
                await self._process_deletion(request_id, user, db)
            
        except Exception as e:
            # Mark request as failed
            await db.execute(
                text("""
                    UPDATE gdpr_requests
                    SET status = 'failed',
                        error_message = :error,
                        completed_at = NOW()
                    WHERE id = :request_id
                """),
                {
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            await db.commit()
    
    async def _process_export(
        self,
        request_id: str,
        user: User,
        db: AsyncSession
    ):
        """Process data export request."""
        
        # Update status
        await db.execute(
            text("""
                UPDATE gdpr_requests
                SET status = 'processing'
                WHERE id = :request_id
            """),
            {"request_id": request_id}
        )
        await db.commit()
        
        # Create temporary directory
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_files = []
            
            # Export each data category
            for table_config in self.export_tables:
                try:
                    data = await self._export_table_data(
                        user.id,
                        table_config,
                        db
                    )
                    
                    if data:
                        filename = f"{table_config['name']}.{table_config['format']}"
                        filepath = os.path.join(temp_dir, filename)
                        
                        if table_config['format'] == 'json':
                            with open(filepath, 'w') as f:
                                json.dump(data, f, indent=2, default=str)
                        elif table_config['format'] == 'csv':
                            await self._write_csv(filepath, data)
                        
                        export_files.append(filepath)
                
                except Exception as e:
                    print(f"Error exporting {table_config['name']}: {e}")
            
            # Add README
            readme_path = os.path.join(temp_dir, "README.txt")
            with open(readme_path, 'w') as f:
                f.write(self._generate_readme(user, request_id))
            export_files.append(readme_path)
            
            # Create ZIP file
            zip_filename = f"tradesense_data_export_{user.id}_{request_id}.zip"
            zip_path = os.path.join(settings.EXPORT_STORAGE_PATH, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in export_files:
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
            
            # Update request with download info
            download_url = f"/api/v1/gdpr/download/{request_id}"
            
            await db.execute(
                text("""
                    UPDATE gdpr_requests
                    SET status = 'completed',
                        completed_at = NOW(),
                        file_path = :file_path,
                        download_url = :download_url
                    WHERE id = :request_id
                """),
                {
                    "request_id": request_id,
                    "file_path": zip_path,
                    "download_url": download_url
                }
            )
            await db.commit()
            
            # Send completion email
            await self._send_export_ready_email(user, request_id, download_url)
    
    async def _process_deletion(
        self,
        request_id: str,
        user: User,
        db: AsyncSession
    ):
        """Process account deletion request."""
        
        # Update status
        await db.execute(
            text("""
                UPDATE gdpr_requests
                SET status = 'processing'
                WHERE id = :request_id
            """),
            {"request_id": request_id}
        )
        await db.commit()
        
        # Cancel active subscriptions
        if user.stripe_subscription_id:
            try:
                import stripe
                stripe.Subscription.delete(user.stripe_subscription_id)
            except:
                pass
        
        # Anonymize user data first
        anonymized_email = f"deleted_user_{user.id}@tradesense.com"
        
        await db.execute(
            text("""
                UPDATE users
                SET email = :email,
                    full_name = 'Deleted User',
                    phone_number = NULL,
                    metadata = '{}'::jsonb,
                    settings = '{}'::jsonb,
                    is_active = FALSE,
                    deleted_at = NOW()
                WHERE id = :user_id
            """),
            {
                "email": anonymized_email,
                "user_id": user.id
            }
        )
        
        # Delete data from related tables
        for table in self.deletion_tables[:-1]:  # Skip users table
            try:
                await db.execute(
                    text(f"""
                        DELETE FROM {table}
                        WHERE user_id = :user_id
                    """),
                    {"user_id": user.id}
                )
            except Exception as e:
                print(f"Error deleting from {table}: {e}")
        
        await db.commit()
        
        # Mark request as completed
        await db.execute(
            text("""
                UPDATE gdpr_requests
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = :request_id
            """),
            {"request_id": request_id}
        )
        await db.commit()
        
        # Send confirmation email
        await self._send_deletion_confirmation(user.email, user.full_name)
    
    async def _export_table_data(
        self,
        user_id: str,
        table_config: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Export data from a specific table."""
        
        result = await db.execute(
            text(table_config["query"]),
            {"user_id": user_id}
        )
        
        rows = []
        for row in result:
            rows.append(dict(row))
        
        return rows
    
    async def _write_csv(self, filepath: str, data: List[Dict[str, Any]]):
        """Write data to CSV file."""
        
        if not data:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _generate_readme(self, user: User, request_id: str) -> str:
        """Generate README file for export."""
        
        return f"""TradeSense Data Export
=====================

Export Request ID: {request_id}
User ID: {user.id}
Email: {user.email}
Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This archive contains all personal data associated with your TradeSense account.

Files Included:
--------------
- user_profile.json: Your account information and settings
- trades.csv: All your trading records
- journal_entries.json: Your trading journal entries
- analytics_events.json: Recent analytics and usage data
- support_tickets.json: Your support ticket history
- payment_history.csv: Your payment and subscription history
- feature_flags.json: Your feature flag settings
- notification_preferences.json: Your notification preferences

Data Formats:
------------
- JSON files: JavaScript Object Notation, readable in any text editor
- CSV files: Comma-separated values, can be opened in Excel or Google Sheets

Privacy Notice:
--------------
This export contains personal data. Please store it securely and do not share
it with unauthorized parties.

This export will be available for download for 30 days.

For questions or concerns, contact: privacy@tradesense.com
"""
    
    async def _send_request_confirmation(
        self,
        user: User,
        request_type: str,
        request_id: str
    ):
        """Send confirmation email for GDPR request."""
        
        subject = f"Your data {request_type} request has been received"
        
        if request_type == "export":
            body = f"""Hi {user.full_name},

We've received your request to export your TradeSense data.

Request ID: {request_id}

We're preparing your data export. This usually takes 1-2 hours. You'll receive another email when your export is ready for download.

The export will include:
- Your profile information
- All trading records
- Journal entries
- Analytics data
- Support tickets
- Payment history
- Settings and preferences

If you didn't make this request, please contact us immediately at security@tradesense.com.

Best regards,
The TradeSense Team"""
        
        else:  # deletion
            body = f"""Hi {user.full_name},

We've received your request to delete your TradeSense account.

Request ID: {request_id}

Your account deletion is being processed. This action will:
- Cancel any active subscriptions
- Permanently delete all your trading data
- Remove your personal information
- Delete all associated records

This process is irreversible. Your account will be fully deleted within 24 hours.

If you didn't make this request or want to cancel it, please contact us immediately at support@tradesense.com.

We're sorry to see you go.

Best regards,
The TradeSense Team"""
        
        await email_service.send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
    
    async def _send_export_ready_email(
        self,
        user: User,
        request_id: str,
        download_url: str
    ):
        """Send email when export is ready."""
        
        await email_service.send_email(
            to_email=user.email,
            subject="Your TradeSense data export is ready",
            body=f"""Hi {user.full_name},

Your data export is ready for download!

Request ID: {request_id}

Download your data: https://app.tradesense.com{download_url}

This export will be available for 30 days. After that, you'll need to submit a new request.

The download is a ZIP file containing all your TradeSense data in various formats (JSON and CSV).

If you have any questions about your data, please contact privacy@tradesense.com.

Best regards,
The TradeSense Team"""
        )
    
    async def _send_deletion_confirmation(
        self,
        email: str,
        name: str
    ):
        """Send final confirmation after account deletion."""
        
        # Send to original email before it was anonymized
        await email_service.send_email(
            to_email=email,
            subject="Your TradeSense account has been deleted",
            body=f"""Hi {name},

Your TradeSense account has been successfully deleted.

All your personal data has been removed from our systems, with the following exceptions:
- Anonymized analytics data for product improvement
- Records required for legal compliance (financial records retained for 7 years)
- This email for confirmation purposes

Your subscription has been cancelled and you will not be charged again.

If you ever want to use TradeSense again, you're welcome to create a new account.

Thank you for using TradeSense.

Best regards,
The TradeSense Team"""
        )


# Initialize service
import uuid
data_export_service = DataExportService()