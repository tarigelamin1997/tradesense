"""
Support ticket management system for TradeSense.
Handles ticket creation, assignment, escalation, and resolution.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session import get_db
from models.user import User
from services.email_service import email_service
from analytics import track_support_event


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    OTHER = "other"


class SupportTicketSystem:
    """Manages support tickets and customer communications."""
    
    def __init__(self):
        self.auto_assign_enabled = True
        self.sla_times = {
            TicketPriority.URGENT: timedelta(hours=2),
            TicketPriority.HIGH: timedelta(hours=8),
            TicketPriority.MEDIUM: timedelta(hours=24),
            TicketPriority.LOW: timedelta(hours=48)
        }
        
        # Auto-response templates
        self.auto_responses = {
            TicketCategory.BILLING: {
                "subject": "Re: {original_subject}",
                "message": """Thank you for contacting TradeSense support.

We've received your billing inquiry and a specialist will review it shortly. 
In the meantime, you can:

1. View your billing history at: https://app.tradesense.com/subscription
2. Update your payment method in the customer portal
3. Check our billing FAQ: https://help.tradesense.com/billing

We typically respond to billing inquiries within 4 business hours.

Best regards,
TradeSense Support Team"""
            },
            TicketCategory.TECHNICAL: {
                "subject": "Re: {original_subject}",
                "message": """Thank you for reporting this technical issue.

We've logged your report and our engineering team will investigate. 
To help us resolve this faster, please provide:

1. Steps to reproduce the issue
2. Expected vs actual behavior
3. Browser/device information
4. Any error messages you see

We'll update you as soon as we have more information.

Best regards,
TradeSense Support Team"""
            }
        }
    
    async def create_ticket(
        self,
        user: User,
        subject: str,
        description: str,
        category: TicketCategory,
        priority: Optional[TicketPriority] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Create a new support ticket."""
        
        # Auto-determine priority if not provided
        if not priority:
            priority = await self._determine_priority(subject, description, user)
        
        ticket_id = str(uuid.uuid4())
        
        # Insert ticket
        await db.execute(
            text("""
                INSERT INTO support_tickets (
                    id, user_id, subject, description, 
                    category, priority, status
                ) VALUES (
                    :id, :user_id, :subject, :description,
                    :category, :priority, :status
                )
            """),
            {
                "id": ticket_id,
                "user_id": user.id,
                "subject": subject,
                "description": description,
                "category": category,
                "priority": priority,
                "status": TicketStatus.OPEN
            }
        )
        
        # Add initial message
        await db.execute(
            text("""
                INSERT INTO support_ticket_messages (
                    ticket_id, user_id, message, attachments
                ) VALUES (
                    :ticket_id, :user_id, :message, :attachments
                )
            """),
            {
                "ticket_id": ticket_id,
                "user_id": user.id,
                "message": description,
                "attachments": attachments
            }
        )
        
        await db.commit()
        
        # Auto-assign if enabled
        if self.auto_assign_enabled:
            assigned_to = await self._auto_assign_ticket(
                ticket_id, category, priority, db
            )
        else:
            assigned_to = None
        
        # Send auto-response
        if category in self.auto_responses:
            await self._send_auto_response(
                user, subject, category, ticket_id
            )
        
        # Track event
        await track_support_event(
            user_id=str(user.id),
            event="ticket_created",
            category=category,
            priority=priority
        )
        
        return {
            "ticket_id": ticket_id,
            "status": TicketStatus.OPEN,
            "assigned_to": assigned_to,
            "created_at": datetime.utcnow()
        }
    
    async def update_ticket(
        self,
        ticket_id: str,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        admin_user: Optional[User] = None,
        db: AsyncSession = None
    ) -> bool:
        """Update ticket details."""
        
        # Build update query
        updates = []
        params = {"ticket_id": ticket_id}
        
        if status:
            updates.append("status = :status")
            params["status"] = status
            
            if status == TicketStatus.RESOLVED:
                updates.append("resolved_at = NOW()")
        
        if priority:
            updates.append("priority = :priority")
            params["priority"] = priority
        
        if assigned_to is not None:
            updates.append("assigned_to = :assigned_to")
            params["assigned_to"] = assigned_to if assigned_to else None
        
        if updates:
            updates.append("updated_at = NOW()")
            
            await db.execute(
                text(f"""
                    UPDATE support_tickets 
                    SET {', '.join(updates)}
                    WHERE id = :ticket_id
                """),
                params
            )
            
            # Log admin action
            if admin_user:
                await self._log_admin_action(
                    admin_user.id,
                    "update_ticket",
                    ticket_id,
                    {"status": status, "priority": priority, "assigned_to": assigned_to},
                    db
                )
            
            await db.commit()
            
            # Send notification if resolved
            if status == TicketStatus.RESOLVED:
                await self._send_resolution_notification(ticket_id, db)
            
            return True
        
        return False
    
    async def add_message(
        self,
        ticket_id: str,
        user: User,
        message: str,
        is_internal: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Add a message to a ticket."""
        
        # Insert message
        result = await db.execute(
            text("""
                INSERT INTO support_ticket_messages (
                    ticket_id, user_id, message, is_internal, attachments
                ) VALUES (
                    :ticket_id, :user_id, :message, :is_internal, :attachments
                )
                RETURNING id, created_at
            """),
            {
                "ticket_id": ticket_id,
                "user_id": user.id,
                "message": message,
                "is_internal": is_internal,
                "attachments": attachments
            }
        )
        
        message_data = result.first()
        
        # Update ticket status if customer replied
        ticket_result = await db.execute(
            text("""
                SELECT user_id, status, assigned_to 
                FROM support_tickets 
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )
        ticket = ticket_result.first()
        
        if ticket:
            # If customer replied to waiting_customer ticket
            if str(user.id) == str(ticket.user_id) and ticket.status == TicketStatus.WAITING_CUSTOMER:
                await db.execute(
                    text("""
                        UPDATE support_tickets 
                        SET status = 'in_progress', updated_at = NOW()
                        WHERE id = :ticket_id
                    """),
                    {"ticket_id": ticket_id}
                )
            
            # If support replied
            elif str(user.id) != str(ticket.user_id) and not is_internal:
                await db.execute(
                    text("""
                        UPDATE support_tickets 
                        SET status = 'waiting_customer', updated_at = NOW()
                        WHERE id = :ticket_id AND status != 'resolved'
                    """),
                    {"ticket_id": ticket_id}
                )
                
                # Send email notification to customer
                await self._send_reply_notification(ticket_id, message, db)
        
        await db.commit()
        
        return {
            "message_id": message_data.id,
            "created_at": message_data.created_at
        }
    
    async def get_tickets(
        self,
        user: Optional[User] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Get tickets with filters."""
        
        # Build query
        where_clauses = []
        params = {"limit": limit, "offset": offset}
        
        if user:
            where_clauses.append("t.user_id = :user_id")
            params["user_id"] = user.id
        
        if status:
            where_clauses.append("t.status = :status")
            params["status"] = status
        
        if priority:
            where_clauses.append("t.priority = :priority")
            params["priority"] = priority
        
        if category:
            where_clauses.append("t.category = :category")
            params["category"] = category
        
        if assigned_to is not None:
            if assigned_to:
                where_clauses.append("t.assigned_to = :assigned_to")
                params["assigned_to"] = assigned_to
            else:
                where_clauses.append("t.assigned_to IS NULL")
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get tickets
        result = await db.execute(
            text(f"""
                SELECT 
                    t.id, t.subject, t.description, t.category,
                    t.priority, t.status, t.created_at, t.updated_at,
                    t.resolved_at, t.assigned_to,
                    u.email as user_email, u.full_name as user_name,
                    a.email as assignee_email, a.full_name as assignee_name,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_message_at
                FROM support_tickets t
                JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                LEFT JOIN support_ticket_messages m ON t.id = m.ticket_id
                {where_clause}
                GROUP BY t.id, u.email, u.full_name, a.email, a.full_name
                ORDER BY 
                    CASE t.priority 
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    t.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        )
        
        tickets = []
        for row in result:
            tickets.append({
                "id": str(row.id),
                "subject": row.subject,
                "description": row.description,
                "category": row.category,
                "priority": row.priority,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "resolved_at": row.resolved_at,
                "user": {
                    "email": row.user_email,
                    "name": row.user_name
                },
                "assignee": {
                    "email": row.assignee_email,
                    "name": row.assignee_name
                } if row.assignee_email else None,
                "message_count": row.message_count,
                "last_message_at": row.last_message_at,
                "sla_deadline": self._calculate_sla_deadline(
                    row.created_at, row.priority
                )
            })
        
        # Get total count
        count_result = await db.execute(
            text(f"""
                SELECT COUNT(*) as total
                FROM support_tickets t
                {where_clause}
            """),
            params
        )
        total = count_result.scalar()
        
        return {
            "tickets": tickets,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_ticket_details(
        self,
        ticket_id: str,
        user: Optional[User] = None,
        db: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed ticket information."""
        
        # Get ticket
        params = {"ticket_id": ticket_id}
        if user and not user.is_admin:
            where_clause = "AND t.user_id = :user_id"
            params["user_id"] = user.id
        else:
            where_clause = ""
        
        result = await db.execute(
            text(f"""
                SELECT 
                    t.*, 
                    u.email as user_email, u.full_name as user_name,
                    u.subscription_tier as user_tier,
                    a.email as assignee_email, a.full_name as assignee_name
                FROM support_tickets t
                JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                WHERE t.id = :ticket_id {where_clause}
            """),
            params
        )
        
        ticket = result.first()
        if not ticket:
            return None
        
        # Get messages
        messages_result = await db.execute(
            text("""
                SELECT 
                    m.id, m.message, m.is_internal, m.attachments,
                    m.created_at, m.user_id,
                    u.email as user_email, u.full_name as user_name,
                    u.is_admin
                FROM support_ticket_messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.ticket_id = :ticket_id
                ORDER BY m.created_at ASC
            """),
            {"ticket_id": ticket_id}
        )
        
        messages = []
        for msg in messages_result:
            # Skip internal messages for non-admin users
            if msg.is_internal and (not user or not user.is_admin):
                continue
                
            messages.append({
                "id": msg.id,
                "message": msg.message,
                "is_internal": msg.is_internal,
                "attachments": msg.attachments,
                "created_at": msg.created_at,
                "user": {
                    "id": str(msg.user_id),
                    "email": msg.user_email,
                    "name": msg.user_name,
                    "is_support": msg.is_admin
                }
            })
        
        return {
            "id": str(ticket.id),
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "resolved_at": ticket.resolved_at,
            "user": {
                "id": str(ticket.user_id),
                "email": ticket.user_email,
                "name": ticket.user_name,
                "tier": ticket.user_tier
            },
            "assignee": {
                "id": str(ticket.assigned_to),
                "email": ticket.assignee_email,
                "name": ticket.assignee_name
            } if ticket.assigned_to else None,
            "messages": messages,
            "sla_deadline": self._calculate_sla_deadline(
                ticket.created_at, ticket.priority
            )
        }
    
    async def search_tickets(
        self,
        query: str,
        user: Optional[User] = None,
        limit: int = 20,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Search tickets by subject or content."""
        
        params = {
            "query": f"%{query}%",
            "limit": limit
        }
        
        if user and not user.is_admin:
            user_clause = "AND t.user_id = :user_id"
            params["user_id"] = user.id
        else:
            user_clause = ""
        
        result = await db.execute(
            text(f"""
                SELECT DISTINCT
                    t.id, t.subject, t.category, t.priority,
                    t.status, t.created_at,
                    u.email as user_email, u.full_name as user_name
                FROM support_tickets t
                JOIN users u ON t.user_id = u.id
                LEFT JOIN support_ticket_messages m ON t.id = m.ticket_id
                WHERE (
                    t.subject ILIKE :query OR
                    t.description ILIKE :query OR
                    m.message ILIKE :query
                ) {user_clause}
                ORDER BY t.created_at DESC
                LIMIT :limit
            """),
            params
        )
        
        tickets = []
        for row in result:
            tickets.append({
                "id": str(row.id),
                "subject": row.subject,
                "category": row.category,
                "priority": row.priority,
                "status": row.status,
                "created_at": row.created_at,
                "user": {
                    "email": row.user_email,
                    "name": row.user_name
                }
            })
        
        return tickets
    
    # Helper methods
    async def _determine_priority(
        self,
        subject: str,
        description: str,
        user: User
    ) -> TicketPriority:
        """Auto-determine ticket priority based on content and user."""
        
        content = f"{subject} {description}".lower()
        
        # Urgent keywords
        urgent_keywords = ["urgent", "critical", "emergency", "down", "broken", "lost access"]
        if any(keyword in content for keyword in urgent_keywords):
            return TicketPriority.URGENT
        
        # High priority for premium users
        if user.subscription_tier == "premium":
            return TicketPriority.HIGH
        
        # High priority keywords
        high_keywords = ["payment", "billing", "charge", "refund", "cancel"]
        if any(keyword in content for keyword in high_keywords):
            return TicketPriority.HIGH
        
        # Default based on user tier
        if user.subscription_tier == "pro":
            return TicketPriority.MEDIUM
        
        return TicketPriority.LOW
    
    async def _auto_assign_ticket(
        self,
        ticket_id: str,
        category: TicketCategory,
        priority: TicketPriority,
        db: AsyncSession
    ) -> Optional[str]:
        """Auto-assign ticket to available support agent."""
        
        # Get available agents based on category specialization
        category_agents = {
            TicketCategory.BILLING: ["billing_team"],
            TicketCategory.TECHNICAL: ["tech_team"],
            TicketCategory.ACCOUNT: ["account_team"]
        }
        
        # For now, return None (manual assignment)
        # In production, implement round-robin or load-based assignment
        return None
    
    async def _send_auto_response(
        self,
        user: User,
        subject: str,
        category: TicketCategory,
        ticket_id: str
    ):
        """Send automatic response email."""
        
        if category not in self.auto_responses:
            return
        
        template = self.auto_responses[category]
        
        await email_service.send_email(
            to_email=user.email,
            subject=template["subject"].format(original_subject=subject),
            body=template["message"],
            metadata={"ticket_id": ticket_id}
        )
    
    async def _send_reply_notification(
        self,
        ticket_id: str,
        message: str,
        db: AsyncSession
    ):
        """Send email notification for ticket reply."""
        
        # Get ticket and user info
        result = await db.execute(
            text("""
                SELECT t.subject, u.email, u.full_name
                FROM support_tickets t
                JOIN users u ON t.user_id = u.id
                WHERE t.id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )
        
        ticket_info = result.first()
        if not ticket_info:
            return
        
        # Send notification
        await email_service.send_email(
            to_email=ticket_info.email,
            subject=f"Re: {ticket_info.subject}",
            body=f"""Hi {ticket_info.full_name},

You have a new reply to your support ticket:

{message[:500]}...

View full conversation: https://app.tradesense.com/support/tickets/{ticket_id}

Best regards,
TradeSense Support Team""",
            metadata={"ticket_id": ticket_id}
        )
    
    async def _send_resolution_notification(
        self,
        ticket_id: str,
        db: AsyncSession
    ):
        """Send notification when ticket is resolved."""
        
        # Get ticket info
        result = await db.execute(
            text("""
                SELECT t.subject, u.email, u.full_name
                FROM support_tickets t
                JOIN users u ON t.user_id = u.id
                WHERE t.id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )
        
        ticket_info = result.first()
        if not ticket_info:
            return
        
        # Send notification
        await email_service.send_email(
            to_email=ticket_info.email,
            subject=f"Resolved: {ticket_info.subject}",
            body=f"""Hi {ticket_info.full_name},

Good news! Your support ticket has been resolved.

If you have any additional questions or if the issue persists, please reply to reopen the ticket.

You can also rate your support experience: https://app.tradesense.com/support/tickets/{ticket_id}/rate

Best regards,
TradeSense Support Team""",
            metadata={"ticket_id": ticket_id}
        )
    
    def _calculate_sla_deadline(
        self,
        created_at: datetime,
        priority: TicketPriority
    ) -> datetime:
        """Calculate SLA deadline based on priority."""
        return created_at + self.sla_times.get(priority, timedelta(hours=48))
    
    async def _log_admin_action(
        self,
        admin_id: str,
        action: str,
        ticket_id: str,
        details: Dict[str, Any],
        db: AsyncSession
    ):
        """Log admin action for audit trail."""
        await db.execute(
            text("""
                INSERT INTO admin_activity_log (
                    admin_id, action, details
                ) VALUES (
                    :admin_id, :action, :details
                )
            """),
            {
                "admin_id": admin_id,
                "action": f"ticket_{action}",
                "details": {
                    "ticket_id": ticket_id,
                    **details
                }
            }
        )


# Initialize support ticket system
ticket_system = SupportTicketSystem()