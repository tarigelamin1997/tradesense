"""
Knowledge base system for TradeSense self-service support.
Provides FAQ, guides, and searchable documentation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import markdown
from bs4 import BeautifulSoup

from core.db.session import get_db
from analytics import track_kb_event


class KnowledgeBase:
    """Manages help articles and documentation."""
    
    def __init__(self):
        # Pre-loaded frequently accessed articles
        self.featured_articles = [
            {
                "id": "getting-started",
                "title": "Getting Started with TradeSense",
                "category": "basics",
                "summary": "Learn how to set up your account and import your first trades"
            },
            {
                "id": "subscription-plans",
                "title": "Understanding Subscription Plans",
                "category": "billing",
                "summary": "Compare features and pricing across our subscription tiers"
            },
            {
                "id": "analytics-guide",
                "title": "Analytics Dashboard Guide",
                "category": "features",
                "summary": "Master the analytics tools to improve your trading"
            }
        ]
        
        # Common questions with instant answers
        self.quick_answers = {
            "reset password": {
                "question": "How do I reset my password?",
                "answer": "Click 'Forgot Password' on the login page. Enter your email and we'll send reset instructions.",
                "article_id": "account-password-reset"
            },
            "change plan": {
                "question": "How do I change my subscription plan?",
                "answer": "Go to Settings > Subscription and click 'Change Plan'. You can upgrade or downgrade anytime.",
                "article_id": "subscription-change-plan"
            },
            "export data": {
                "question": "How do I export my trade data?",
                "answer": "Go to Analytics > Export Data. Choose your format (CSV/Excel) and date range.",
                "article_id": "data-export-guide"
            },
            "api access": {
                "question": "How do I get API access?",
                "answer": "API access is available on Pro and Premium plans. Generate keys in Settings > API.",
                "article_id": "api-getting-started"
            }
        }
        
        # Article templates
        self.article_templates = {
            "troubleshooting": {
                "sections": ["Problem", "Common Causes", "Solutions", "Prevention"]
            },
            "how-to": {
                "sections": ["Overview", "Prerequisites", "Steps", "Tips"]
            },
            "feature": {
                "sections": ["What it does", "How to use it", "Best practices", "Examples"]
            }
        }
    
    async def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base articles."""
        
        # First check quick answers
        quick_results = []
        query_lower = query.lower()
        
        for keyword, qa in self.quick_answers.items():
            if keyword in query_lower:
                quick_results.append({
                    "type": "quick_answer",
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "article_id": qa["article_id"],
                    "relevance": 1.0
                })
        
        # Search articles in database
        params = {
            "query": f"%{query}%",
            "limit": limit - len(quick_results)
        }
        
        category_clause = ""
        if category:
            category_clause = "AND category = :category"
            params["category"] = category
        
        result = await db.execute(
            text(f"""
                SELECT 
                    id, title, slug, category, summary,
                    tags, view_count, helpful_count, 
                    not_helpful_count, updated_at,
                    ts_rank(search_vector, plainto_tsquery('english', :search_query)) as rank
                FROM kb_articles
                WHERE 
                    (search_vector @@ plainto_tsquery('english', :search_query)
                    OR title ILIKE :query
                    OR summary ILIKE :query)
                    AND is_published = true
                    {category_clause}
                ORDER BY rank DESC, view_count DESC
                LIMIT :limit
            """),
            {**params, "search_query": query}
        )
        
        articles = []
        for row in result:
            articles.append({
                "type": "article",
                "id": str(row.id),
                "title": row.title,
                "slug": row.slug,
                "category": row.category,
                "summary": row.summary,
                "tags": row.tags,
                "view_count": row.view_count,
                "helpful_rate": self._calculate_helpful_rate(
                    row.helpful_count, row.not_helpful_count
                ),
                "updated_at": row.updated_at,
                "relevance": float(row.rank) if row.rank else 0.5
            })
        
        # Track search
        await track_kb_event(
            event="search",
            query=query,
            results_count=len(quick_results) + len(articles)
        )
        
        # Combine and sort by relevance
        all_results = quick_results + articles
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return all_results[:limit]
    
    async def get_article(
        self,
        article_id: str,
        increment_views: bool = True,
        db: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """Get article content by ID or slug."""
        
        # Check if it's an ID or slug
        if '-' in article_id and not article_id.startswith('00000000'):
            where_clause = "slug = :identifier"
        else:
            where_clause = "id = :identifier"
        
        result = await db.execute(
            text(f"""
                SELECT 
                    id, title, slug, category, summary,
                    content, tags, author_id, 
                    view_count, helpful_count, not_helpful_count,
                    created_at, updated_at, 
                    related_articles, attachments
                FROM kb_articles
                WHERE {where_clause} AND is_published = true
            """),
            {"identifier": article_id}
        )
        
        article = result.first()
        if not article:
            return None
        
        # Increment view count
        if increment_views:
            await db.execute(
                text("""
                    UPDATE kb_articles 
                    SET view_count = view_count + 1 
                    WHERE id = :id
                """),
                {"id": article.id}
            )
            await db.commit()
        
        # Parse markdown content to HTML
        html_content = markdown.markdown(
            article.content,
            extensions=['extra', 'codehilite', 'toc']
        )
        
        # Get related articles
        related = []
        if article.related_articles:
            related_result = await db.execute(
                text("""
                    SELECT id, title, slug, category, summary
                    FROM kb_articles
                    WHERE id = ANY(:ids) AND is_published = true
                """),
                {"ids": article.related_articles}
            )
            
            for row in related_result:
                related.append({
                    "id": str(row.id),
                    "title": row.title,
                    "slug": row.slug,
                    "category": row.category,
                    "summary": row.summary
                })
        
        # Track view
        await track_kb_event(
            event="view_article",
            article_id=str(article.id),
            category=article.category
        )
        
        return {
            "id": str(article.id),
            "title": article.title,
            "slug": article.slug,
            "category": article.category,
            "summary": article.summary,
            "content": article.content,
            "html_content": html_content,
            "tags": article.tags,
            "view_count": article.view_count + 1,
            "helpful_rate": self._calculate_helpful_rate(
                article.helpful_count, article.not_helpful_count
            ),
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "related_articles": related,
            "attachments": article.attachments,
            "estimated_read_time": self._estimate_read_time(article.content)
        }
    
    async def get_categories(
        self,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get all article categories with counts."""
        
        result = await db.execute(
            text("""
                SELECT 
                    category,
                    COUNT(*) as article_count,
                    SUM(view_count) as total_views
                FROM kb_articles
                WHERE is_published = true
                GROUP BY category
                ORDER BY article_count DESC
            """)
        )
        
        categories = []
        category_info = {
            "basics": {
                "name": "Getting Started",
                "icon": "rocket",
                "description": "New to TradeSense? Start here"
            },
            "features": {
                "name": "Features & Tools",
                "icon": "tools",
                "description": "Learn about our powerful features"
            },
            "billing": {
                "name": "Billing & Subscriptions",
                "icon": "credit-card",
                "description": "Payment and plan information"
            },
            "api": {
                "name": "API & Integrations",
                "icon": "code",
                "description": "Developer documentation"
            },
            "troubleshooting": {
                "name": "Troubleshooting",
                "icon": "wrench",
                "description": "Solve common issues"
            }
        }
        
        for row in result:
            info = category_info.get(row.category, {
                "name": row.category.title(),
                "icon": "file-text",
                "description": ""
            })
            
            categories.append({
                "id": row.category,
                "name": info["name"],
                "icon": info["icon"],
                "description": info["description"],
                "article_count": row.article_count,
                "total_views": row.total_views
            })
        
        return categories
    
    async def get_popular_articles(
        self,
        category: Optional[str] = None,
        limit: int = 5,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get most viewed articles."""
        
        params = {"limit": limit}
        category_clause = ""
        
        if category:
            category_clause = "AND category = :category"
            params["category"] = category
        
        result = await db.execute(
            text(f"""
                SELECT 
                    id, title, slug, category, summary,
                    view_count, helpful_count, not_helpful_count
                FROM kb_articles
                WHERE is_published = true {category_clause}
                ORDER BY view_count DESC
                LIMIT :limit
            """),
            params
        )
        
        articles = []
        for row in result:
            articles.append({
                "id": str(row.id),
                "title": row.title,
                "slug": row.slug,
                "category": row.category,
                "summary": row.summary,
                "view_count": row.view_count,
                "helpful_rate": self._calculate_helpful_rate(
                    row.helpful_count, row.not_helpful_count
                )
            })
        
        return articles
    
    async def rate_article(
        self,
        article_id: str,
        helpful: bool,
        user_id: Optional[str] = None,
        feedback: Optional[str] = None,
        db: AsyncSession = None
    ) -> bool:
        """Rate article as helpful or not helpful."""
        
        # Check if user already rated (if user_id provided)
        if user_id:
            existing = await db.execute(
                text("""
                    SELECT id FROM kb_article_ratings
                    WHERE article_id = :article_id AND user_id = :user_id
                """),
                {"article_id": article_id, "user_id": user_id}
            )
            
            if existing.first():
                # Update existing rating
                await db.execute(
                    text("""
                        UPDATE kb_article_ratings
                        SET helpful = :helpful, feedback = :feedback,
                            updated_at = NOW()
                        WHERE article_id = :article_id AND user_id = :user_id
                    """),
                    {
                        "article_id": article_id,
                        "user_id": user_id,
                        "helpful": helpful,
                        "feedback": feedback
                    }
                )
            else:
                # Create new rating
                await db.execute(
                    text("""
                        INSERT INTO kb_article_ratings
                        (article_id, user_id, helpful, feedback)
                        VALUES (:article_id, :user_id, :helpful, :feedback)
                    """),
                    {
                        "article_id": article_id,
                        "user_id": user_id,
                        "helpful": helpful,
                        "feedback": feedback
                    }
                )
        
        # Update article counts
        if helpful:
            column = "helpful_count = helpful_count + 1"
        else:
            column = "not_helpful_count = not_helpful_count + 1"
        
        await db.execute(
            text(f"""
                UPDATE kb_articles
                SET {column}
                WHERE id = :article_id
            """),
            {"article_id": article_id}
        )
        
        await db.commit()
        
        # Track rating
        await track_kb_event(
            event="rate_article",
            article_id=article_id,
            helpful=helpful,
            user_id=user_id
        )
        
        return True
    
    async def suggest_articles_for_ticket(
        self,
        ticket_subject: str,
        ticket_description: str,
        limit: int = 3,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Suggest relevant articles for a support ticket."""
        
        # Combine subject and description for better search
        search_text = f"{ticket_subject} {ticket_description}"
        
        # Search for relevant articles
        articles = await self.search_articles(
            query=search_text,
            limit=limit,
            db=db
        )
        
        # Filter to only highly relevant results
        relevant_articles = [
            article for article in articles
            if article.get("relevance", 0) > 0.3
        ]
        
        return relevant_articles
    
    async def create_article(
        self,
        title: str,
        content: str,
        category: str,
        summary: str,
        tags: List[str],
        author_id: str,
        is_published: bool = False,
        related_articles: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> str:
        """Create a new knowledge base article (admin only)."""
        
        article_id = str(uuid.uuid4())
        slug = self._generate_slug(title)
        
        # Generate search vector from content
        search_text = f"{title} {summary} {content} {' '.join(tags)}"
        
        await db.execute(
            text("""
                INSERT INTO kb_articles (
                    id, title, slug, category, summary,
                    content, tags, author_id, is_published,
                    related_articles, search_vector
                ) VALUES (
                    :id, :title, :slug, :category, :summary,
                    :content, :tags, :author_id, :is_published,
                    :related_articles, to_tsvector('english', :search_text)
                )
            """),
            {
                "id": article_id,
                "title": title,
                "slug": slug,
                "category": category,
                "summary": summary,
                "content": content,
                "tags": tags,
                "author_id": author_id,
                "is_published": is_published,
                "related_articles": related_articles,
                "search_text": search_text
            }
        )
        
        await db.commit()
        
        return article_id
    
    # Helper methods
    def _calculate_helpful_rate(
        self,
        helpful_count: int,
        not_helpful_count: int
    ) -> float:
        """Calculate helpfulness percentage."""
        total = helpful_count + not_helpful_count
        if total == 0:
            return 0.0
        return (helpful_count / total) * 100
    
    def _estimate_read_time(self, content: str) -> int:
        """Estimate reading time in minutes."""
        # Remove markdown and HTML
        soup = BeautifulSoup(
            markdown.markdown(content),
            'html.parser'
        )
        text = soup.get_text()
        
        # Average reading speed: 200-250 words per minute
        word_count = len(text.split())
        return max(1, round(word_count / 225))
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        import re
        
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        return slug


# Initialize knowledge base
knowledge_base = KnowledgeBase()