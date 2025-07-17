"""
Support API endpoints for TradeSense.
Handles tickets, knowledge base, and customer communications.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_admin
from app.core.db.session import get_db
from app.models.user import User
from src.backend.support.ticket_system import (
    ticket_system, TicketStatus, TicketPriority, TicketCategory
)
from src.backend.support.knowledge_base import knowledge_base
from src.backend.analytics import track_feature_usage

router = APIRouter(prefix="/api/v1/support", tags=["support"])


# Request models
class CreateTicketRequest(BaseModel):
    subject: str
    description: str
    category: TicketCategory
    priority: Optional[TicketPriority] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class UpdateTicketRequest(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None


class AddMessageRequest(BaseModel):
    message: str
    is_internal: bool = False
    attachments: Optional[List[Dict[str, Any]]] = None


class RateArticleRequest(BaseModel):
    helpful: bool
    feedback: Optional[str] = None


# Ticket endpoints
@router.post("/tickets")
async def create_ticket(
    ticket_data: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new support ticket."""
    try:
        # Check for suggested articles first
        suggestions = await knowledge_base.suggest_articles_for_ticket(
            ticket_subject=ticket_data.subject,
            ticket_description=ticket_data.description,
            db=db
        )
        
        # Create ticket
        result = await ticket_system.create_ticket(
            user=current_user,
            subject=ticket_data.subject,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=ticket_data.priority,
            attachments=ticket_data.attachments,
            db=db
        )
        
        # Track usage
        await track_feature_usage(
            str(current_user.id),
            "create_support_ticket"
        )
        
        return {
            "ticket": result,
            "suggested_articles": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets")
async def get_tickets(
    status: Optional[TicketStatus] = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    category: Optional[TicketCategory] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tickets for current user or all tickets for admin."""
    try:
        if current_user.is_admin:
            # Admin can see all tickets
            user = None
        else:
            # Regular users see only their tickets
            user = current_user
            assigned_to = None  # Regular users can't filter by assignee
        
        result = await ticket_system.get_tickets(
            user=user,
            status=status,
            priority=priority,
            category=category,
            assigned_to=assigned_to,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{ticket_id}")
async def get_ticket_details(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed ticket information."""
    try:
        details = await ticket_system.get_ticket_details(
            ticket_id=ticket_id,
            user=current_user,
            db=db
        )
        
        if not details:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    update_data: UpdateTicketRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update ticket details (admin only)."""
    try:
        success = await ticket_system.update_ticket(
            ticket_id=ticket_id,
            status=update_data.status,
            priority=update_data.priority,
            assigned_to=update_data.assigned_to,
            admin_user=current_user,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update ticket")
        
        return {"message": "Ticket updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickets/{ticket_id}/messages")
async def add_ticket_message(
    ticket_id: str,
    message_data: AddMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a ticket."""
    try:
        # Verify user has access to ticket
        ticket = await ticket_system.get_ticket_details(
            ticket_id=ticket_id,
            user=current_user,
            db=db
        )
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Only admins can add internal messages
        if message_data.is_internal and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admins can add internal notes")
        
        result = await ticket_system.add_message(
            ticket_id=ticket_id,
            user=current_user,
            message=message_data.message,
            is_internal=message_data.is_internal,
            attachments=message_data.attachments,
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/search")
async def search_tickets(
    q: str = Query(..., min_length=3),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search tickets by subject or content."""
    try:
        results = await ticket_system.search_tickets(
            query=q,
            user=current_user,
            limit=limit,
            db=db
        )
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge base endpoints
@router.get("/kb/search")
async def search_knowledge_base(
    q: str = Query(..., min_length=2),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search knowledge base articles."""
    try:
        results = await knowledge_base.search_articles(
            query=q,
            category=category,
            limit=limit,
            db=db
        )
        
        # Track search
        await track_feature_usage(
            "anonymous",
            "search_knowledge_base"
        )
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/categories")
async def get_kb_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all knowledge base categories."""
    try:
        categories = await knowledge_base.get_categories(db=db)
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/articles/popular")
async def get_popular_articles(
    category: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get most viewed articles."""
    try:
        articles = await knowledge_base.get_popular_articles(
            category=category,
            limit=limit,
            db=db
        )
        
        return {"articles": articles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/articles/{article_id}")
async def get_kb_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get knowledge base article by ID or slug."""
    try:
        article = await knowledge_base.get_article(
            article_id=article_id,
            increment_views=True,
            db=db
        )
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return article
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/articles/{article_id}/rate")
async def rate_kb_article(
    article_id: str,
    rating_data: RateArticleRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate a knowledge base article."""
    try:
        user_id = str(current_user.id) if current_user else None
        
        success = await knowledge_base.rate_article(
            article_id=article_id,
            helpful=rating_data.helpful,
            user_id=user_id,
            feedback=rating_data.feedback,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to rate article")
        
        return {"message": "Thank you for your feedback"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints for knowledge base
@router.post("/kb/articles")
async def create_kb_article(
    title: str = Body(...),
    content: str = Body(...),
    category: str = Body(...),
    summary: str = Body(...),
    tags: List[str] = Body(...),
    is_published: bool = Body(False),
    related_articles: Optional[List[str]] = Body(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge base article (admin only)."""
    try:
        article_id = await knowledge_base.create_article(
            title=title,
            content=content,
            category=category,
            summary=summary,
            tags=tags,
            author_id=str(current_user.id),
            is_published=is_published,
            related_articles=related_articles,
            db=db
        )
        
        return {
            "article_id": article_id,
            "message": "Article created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Support statistics (admin only)
@router.get("/stats")
async def get_support_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get support system statistics."""
    try:
        # Get ticket stats
        ticket_stats = await db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tickets,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
                    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent_tickets,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as new_today,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600)::float as avg_resolution_hours
                FROM support_tickets
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
        )
        
        stats = ticket_stats.first()
        
        # Get KB stats
        kb_stats = await db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_articles,
                    SUM(view_count) as total_views,
                    AVG(CASE WHEN helpful_count + not_helpful_count > 0 
                        THEN helpful_count::float / (helpful_count + not_helpful_count) * 100 
                        ELSE NULL END) as avg_helpful_rate
                FROM kb_articles
                WHERE is_published = true
            """)
        )
        
        kb = kb_stats.first()
        
        # Get agent performance
        agent_stats = await db.execute(
            text("""
                SELECT 
                    u.email,
                    COUNT(t.id) as tickets_handled,
                    AVG(EXTRACT(EPOCH FROM (t.resolved_at - t.created_at))/3600)::float as avg_resolution_hours
                FROM support_tickets t
                JOIN users u ON t.assigned_to = u.id
                WHERE t.resolved_at IS NOT NULL
                AND t.created_at > NOW() - INTERVAL '30 days'
                GROUP BY u.email
                ORDER BY tickets_handled DESC
                LIMIT 10
            """)
        )
        
        top_agents = []
        for agent in agent_stats:
            top_agents.append({
                "email": agent.email,
                "tickets_handled": agent.tickets_handled,
                "avg_resolution_hours": round(agent.avg_resolution_hours, 1) if agent.avg_resolution_hours else None
            })
        
        return {
            "tickets": {
                "total": stats.total_tickets,
                "open": stats.open_tickets,
                "in_progress": stats.in_progress_tickets,
                "resolved": stats.resolved_tickets,
                "urgent": stats.urgent_tickets,
                "new_today": stats.new_today,
                "avg_resolution_hours": round(stats.avg_resolution_hours, 1) if stats.avg_resolution_hours else None
            },
            "knowledge_base": {
                "total_articles": kb.total_articles,
                "total_views": kb.total_views,
                "avg_helpful_rate": round(kb.avg_helpful_rate, 1) if kb.avg_helpful_rate else None
            },
            "top_agents": top_agents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))