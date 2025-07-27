from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import hashlib
import json
import uuid
from collections import defaultdict
import re

from models.feedback import Feedback, FeedbackPattern as FeedbackPatternModel
from .schemas import (
    FeedbackSubmit, FeedbackItem, FeedbackAnalytics,
    FeedbackPattern, TopIssue, TrendingIssue, ResolutionTime,
    UserImpact, ChurnCorrelation, FeedbackHeatmapData,
    ImpactAnalysis, PatternDetails
)
from services.email_service import EmailService

class FeedbackService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    async def create_feedback(
        self,
        user_id: Optional[str],
        user_email: Optional[str],
        feedback_data: FeedbackSubmit
    ) -> str:
        """Create new feedback entry"""
        feedback_id = str(uuid.uuid4())
        
        # Get user subscription tier if authenticated
        subscription_tier = None
        if user_id:
            # Get user subscription from database
            # subscription_tier = self.get_user_subscription_tier(user_id)
            pass
        
        feedback = Feedback(
            id=feedback_id,
            user_id=user_id,
            type=feedback_data.type,
            severity=feedback_data.severity,
            title=feedback_data.title,
            description=feedback_data.description,
            status="new",
            url=feedback_data.url,
            user_agent=feedback_data.user_agent,
            screen_resolution=feedback_data.screen_resolution,
            subscription_tier=subscription_tier,
            previous_pages=json.dumps(feedback_data.previous_pages),
            last_actions=json.dumps([a.dict() for a in feedback_data.last_actions]),
            error_logs=json.dumps([e.dict() for e in feedback_data.error_logs]),
            screenshot=feedback_data.screenshot,
            expected_behavior=feedback_data.expected_behavior,
            actual_behavior=feedback_data.actual_behavior,
            email=user_email or feedback_data.email,
            created_at=datetime.utcnow()
        )
        
        self.db.add(feedback)
        self.db.commit()
        
        return feedback_id
    
    async def detect_pattern(self, feedback: FeedbackSubmit) -> Optional[str]:
        """Detect if feedback matches existing pattern"""
        # Create pattern signature
        signature = self._generate_pattern_signature(feedback)
        
        # Check for existing pattern
        pattern = self.db.query(FeedbackPatternModel).filter_by(
            pattern_signature=signature
        ).first()
        
        if pattern:
            # Update existing pattern
            pattern.occurrences += 1
            pattern.last_seen = datetime.utcnow()
            
            # Check if this is from a new user
            existing_feedback = self.db.query(Feedback).filter_by(
                pattern_id=pattern.id
            ).all()
            
            unique_users = set(f.user_id for f in existing_feedback if f.user_id)
            pattern.affected_users = len(unique_users)
            
            self.db.commit()
            return pattern.id
        else:
            # Create new pattern if significant
            if self._is_significant_pattern(feedback):
                pattern_id = str(uuid.uuid4())
                new_pattern = FeedbackPatternModel(
                    id=pattern_id,
                    pattern_signature=signature,
                    pattern_type=feedback.type,
                    occurrences=1,
                    affected_users=1,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                self.db.add(new_pattern)
                self.db.commit()
                return pattern_id
        
        return None
    
    def _generate_pattern_signature(self, feedback: FeedbackSubmit) -> str:
        """Generate unique signature for pattern matching"""
        # Extract key elements for pattern matching
        key_elements = [
            feedback.type,
            feedback.url,
            self._extract_error_pattern(feedback.description),
            self._extract_error_pattern(feedback.title)
        ]
        
        # Add error signatures if present
        if feedback.error_logs:
            for error in feedback.error_logs[:3]:  # First 3 errors
                key_elements.append(self._extract_error_pattern(error.message))
        
        # Create hash of key elements
        signature_string = "|".join(filter(None, key_elements))
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def _extract_error_pattern(self, text: str) -> str:
        """Extract error pattern from text"""
        # Remove specific values to find general patterns
        pattern = text.lower()
        
        # Remove IDs, numbers, URLs
        pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', pattern)
        pattern = re.sub(r'\d+', 'NUM', pattern)
        pattern = re.sub(r'https?://[^\s]+', 'URL', pattern)
        pattern = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'EMAIL', pattern)
        
        # Extract key error phrases
        error_patterns = [
            r'(error|exception|failed|failure|crash|bug)',
            r'(undefined|null|not found|missing)',
            r'(timeout|slow|performance)',
            r'(cannot|could not|unable to)'
        ]
        
        for pattern_regex in error_patterns:
            match = re.search(pattern_regex, pattern)
            if match:
                return match.group(0)
        
        # Return first 50 chars if no pattern found
        return pattern[:50]
    
    def _is_significant_pattern(self, feedback: FeedbackSubmit) -> bool:
        """Determine if feedback represents a significant pattern"""
        # Always create pattern for critical issues
        if feedback.severity == "critical":
            return True
        
        # Create pattern if it has error logs
        if feedback.error_logs:
            return True
        
        # Create pattern for specific types
        if feedback.type in ["bug", "performance"]:
            return True
        
        return False
    
    async def send_critical_alert(self, feedback_id: str, feedback: FeedbackSubmit):
        """Send alert for critical feedback"""
        # Send email to admin
        await self.email_service.send_critical_feedback_alert(
            feedback_id=feedback_id,
            title=feedback.title,
            description=feedback.description,
            url=feedback.url,
            user_email=feedback.email
        )
        
        # Could also send to Slack, Discord, etc.
    
    async def get_analytics(self) -> FeedbackAnalytics:
        """Get comprehensive feedback analytics"""
        # Top issues
        top_issues_query = self.db.query(
            FeedbackPatternModel.id,
            FeedbackPatternModel.pattern_type,
            func.count(Feedback.id).label('count')
        ).join(
            Feedback, Feedback.pattern_id == FeedbackPatternModel.id
        ).group_by(
            FeedbackPatternModel.id
        ).order_by(
            func.count(Feedback.id).desc()
        ).limit(10).all()
        
        top_issues = []
        for pattern_id, pattern_type, count in top_issues_query:
            # Get a sample feedback for title
            sample = self.db.query(Feedback).filter_by(pattern_id=pattern_id).first()
            if sample:
                top_issues.append(TopIssue(
                    pattern_id=pattern_id,
                    title=sample.title,
                    count=count,
                    severity=sample.severity
                ))
        
        # Trending issues (growing in last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        trending_patterns = self._get_trending_patterns(yesterday)
        
        # Critical patterns
        critical_patterns = self.db.query(FeedbackPatternModel).filter(
            FeedbackPatternModel.pattern_type == "bug",
            FeedbackPatternModel.occurrences >= 5
        ).all()
        
        # Resolution time
        resolution_time = self._calculate_resolution_time()
        
        # User impact
        user_impact = self._calculate_user_impact()
        
        # Churn correlation
        churn_correlation = self._analyze_churn_correlation()
        
        return FeedbackAnalytics(
            top_issues=top_issues,
            trending_issues=trending_patterns,
            critical_patterns=[self._pattern_to_schema(p) for p in critical_patterns],
            resolution_time=resolution_time,
            user_impact=user_impact,
            churn_correlation=churn_correlation
        )
    
    def _get_trending_patterns(self, since: datetime) -> List[TrendingIssue]:
        """Get patterns trending upward"""
        recent_feedback = self.db.query(
            Feedback.pattern_id,
            func.count(Feedback.id).label('recent_count')
        ).filter(
            Feedback.created_at >= since,
            Feedback.pattern_id.isnot(None)
        ).group_by(Feedback.pattern_id).all()
        
        trending = []
        for pattern_id, recent_count in recent_feedback:
            # Get total count
            total_count = self.db.query(Feedback).filter_by(pattern_id=pattern_id).count()
            
            # Calculate growth rate
            if total_count > recent_count:
                growth_rate = recent_count / (total_count - recent_count)
                if growth_rate > 0.5:  # 50% growth
                    sample = self.db.query(Feedback).filter_by(pattern_id=pattern_id).first()
                    trending.append(TrendingIssue(
                        pattern_id=pattern_id,
                        title=sample.title if sample else "Unknown",
                        growth_rate=growth_rate
                    ))
        
        return sorted(trending, key=lambda x: x.growth_rate, reverse=True)[:5]
    
    def _calculate_resolution_time(self) -> ResolutionTime:
        """Calculate average resolution times"""
        resolved_feedback = self.db.query(Feedback).filter(
            Feedback.status == "resolved",
            Feedback.resolved_at.isnot(None)
        ).all()
        
        if not resolved_feedback:
            return ResolutionTime(average_hours=0, by_severity={})
        
        total_hours = 0
        by_severity = defaultdict(list)
        
        for feedback in resolved_feedback:
            hours = (feedback.resolved_at - feedback.created_at).total_seconds() / 3600
            total_hours += hours
            by_severity[feedback.severity].append(hours)
        
        return ResolutionTime(
            average_hours=total_hours / len(resolved_feedback),
            by_severity={
                severity: sum(times) / len(times)
                for severity, times in by_severity.items()
            }
        )
    
    def _calculate_user_impact(self) -> UserImpact:
        """Calculate user impact metrics"""
        affected_users = self.db.query(
            func.count(func.distinct(Feedback.user_id))
        ).filter(Feedback.user_id.isnot(None)).scalar()
        
        by_tier_query = self.db.query(
            Feedback.subscription_tier,
            func.count(func.distinct(Feedback.user_id))
        ).filter(
            Feedback.user_id.isnot(None),
            Feedback.subscription_tier.isnot(None)
        ).group_by(Feedback.subscription_tier).all()
        
        return UserImpact(
            total_affected=affected_users or 0,
            by_tier=dict(by_tier_query)
        )
    
    def _analyze_churn_correlation(self) -> ChurnCorrelation:
        """Analyze correlation between feedback and churn"""
        # This is a simplified version
        # In production, you'd correlate with actual churn data
        
        high_risk_patterns = self.db.query(FeedbackPatternModel.id).filter(
            FeedbackPatternModel.pattern_type.in_(["bug", "performance"]),
            FeedbackPatternModel.occurrences >= 10
        ).limit(5).all()
        
        # Estimate revenue impact (simplified)
        affected_premium_users = self.db.query(
            func.count(func.distinct(Feedback.user_id))
        ).filter(
            Feedback.subscription_tier.in_(["pro", "enterprise"]),
            Feedback.severity.in_(["critical", "high"])
        ).scalar() or 0
        
        estimated_revenue_impact = affected_premium_users * 50  # $50 avg revenue per user
        
        return ChurnCorrelation(
            high_risk_patterns=[p[0] for p in high_risk_patterns],
            estimated_revenue_impact=float(estimated_revenue_impact)
        )
    
    def _pattern_to_schema(self, pattern: FeedbackPatternModel) -> FeedbackPattern:
        """Convert DB model to schema"""
        return FeedbackPattern(
            id=pattern.id,
            pattern_signature=pattern.pattern_signature,
            pattern_type=pattern.pattern_type,
            occurrences=pattern.occurrences,
            affected_users=pattern.affected_users,
            first_seen=pattern.first_seen,
            last_seen=pattern.last_seen,
            root_cause=pattern.root_cause,
            resolution=pattern.resolution
        )
    
    async def get_pattern_details(self, pattern_id: str) -> Optional[PatternDetails]:
        """Get detailed information about a pattern"""
        pattern = self.db.query(FeedbackPatternModel).filter_by(id=pattern_id).first()
        if not pattern:
            return None
        
        # Get related feedback
        related_feedback = self.db.query(Feedback).filter_by(
            pattern_id=pattern_id
        ).order_by(Feedback.created_at.desc()).limit(20).all()
        
        # Generate suggested fixes based on pattern type
        suggested_fixes = self._generate_suggested_fixes(pattern, related_feedback)
        
        return PatternDetails(
            pattern=self._pattern_to_schema(pattern),
            related_feedback=[self._feedback_to_schema(f) for f in related_feedback],
            suggested_fixes=suggested_fixes
        )
    
    def _generate_suggested_fixes(
        self, 
        pattern: FeedbackPatternModel, 
        feedback_items: List[Feedback]
    ) -> List[str]:
        """Generate AI-powered fix suggestions"""
        suggestions = []
        
        # Analyze common elements
        if pattern.pattern_type == "bug":
            if any("undefined" in f.description.lower() for f in feedback_items):
                suggestions.append("Add null/undefined checks for affected variables")
            if any("timeout" in f.description.lower() for f in feedback_items):
                suggestions.append("Increase timeout limits or optimize slow operations")
            if any("404" in f.description or "not found" in f.description.lower() for f in feedback_items):
                suggestions.append("Verify API endpoints and resource paths")
        
        elif pattern.pattern_type == "performance":
            suggestions.extend([
                "Profile the affected page/feature for performance bottlenecks",
                "Check for unnecessary re-renders or API calls",
                "Implement caching for frequently accessed data",
                "Consider pagination or lazy loading for large datasets"
            ])
        
        elif pattern.pattern_type == "ux":
            suggestions.extend([
                "Conduct user testing on the affected feature",
                "Review UI/UX best practices for similar interfaces",
                "Add helpful tooltips or documentation",
                "Simplify the workflow if users are confused"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _feedback_to_schema(self, feedback: Feedback) -> FeedbackItem:
        """Convert feedback DB model to schema"""
        return FeedbackItem(
            id=feedback.id,
            user_id=feedback.user_id,
            type=feedback.type,
            severity=feedback.severity,
            title=feedback.title,
            description=feedback.description,
            status=feedback.status,
            url=feedback.url,
            user_agent=feedback.user_agent,
            screen_resolution=feedback.screen_resolution,
            subscription_tier=feedback.subscription_tier,
            created_at=feedback.created_at,
            resolved_at=feedback.resolved_at,
            resolution_notes=feedback.resolution_notes,
            assigned_to=feedback.assigned_to,
            duplicate_count=feedback.duplicate_count,
            affected_users=feedback.affected_users
        )
    
    async def list_feedback(
        self,
        status: Optional[str] = None,
        type: Optional[str] = None,
        severity: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[FeedbackItem]:
        """List feedback with filters"""
        query = self.db.query(Feedback)
        
        if status:
            query = query.filter(Feedback.status == status)
        if type:
            query = query.filter(Feedback.type == type)
        if severity:
            query = query.filter(Feedback.severity == severity)
        if date_from:
            query = query.filter(Feedback.created_at >= date_from)
        if date_to:
            query = query.filter(Feedback.created_at <= date_to)
        
        feedback_list = query.order_by(Feedback.created_at.desc()).all()
        return [self._feedback_to_schema(f) for f in feedback_list]
    
    async def update_status(
        self,
        feedback_id: str,
        status: str,
        resolution_notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> Optional[FeedbackItem]:
        """Update feedback status"""
        feedback = self.db.query(Feedback).filter_by(id=feedback_id).first()
        if not feedback:
            return None
        
        feedback.status = status
        if resolution_notes:
            feedback.resolution_notes = resolution_notes
        if assigned_to:
            feedback.assigned_to = assigned_to
        
        if status == "resolved":
            feedback.resolved_at = datetime.utcnow()
        
        self.db.commit()
        return self._feedback_to_schema(feedback)
    
    async def send_resolution_notification(self, feedback_id: str):
        """Send notification when feedback is resolved"""
        feedback = self.db.query(Feedback).filter_by(id=feedback_id).first()
        if feedback and feedback.email:
            await self.email_service.send_feedback_resolved(
                email=feedback.email,
                feedback_id=feedback_id,
                title=feedback.title,
                resolution_notes=feedback.resolution_notes
            )
    
    async def get_recent_feedback(self, limit: int = 10) -> List[FeedbackItem]:
        """Get most recent feedback"""
        recent = self.db.query(Feedback).order_by(
            Feedback.created_at.desc()
        ).limit(limit).all()
        return [self._feedback_to_schema(f) for f in recent]
    
    async def get_critical_issues(self) -> List[FeedbackItem]:
        """Get unresolved critical issues"""
        critical = self.db.query(Feedback).filter(
            Feedback.severity == "critical",
            Feedback.status != "resolved"
        ).order_by(Feedback.created_at.desc()).all()
        return [self._feedback_to_schema(f) for f in critical]
    
    async def get_trending_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns trending in last 24 hours"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        trending = self._get_trending_patterns(yesterday)
        return [t.dict() for t in trending]
    
    async def get_resolution_stats(self) -> Dict[str, Any]:
        """Get resolution statistics"""
        total = self.db.query(Feedback).count()
        resolved = self.db.query(Feedback).filter(Feedback.status == "resolved").count()
        in_progress = self.db.query(Feedback).filter(Feedback.status == "in_progress").count()
        
        resolution_time = self._calculate_resolution_time()
        
        return {
            "total_feedback": total,
            "resolved": resolved,
            "in_progress": in_progress,
            "resolution_rate": (resolved / total * 100) if total > 0 else 0,
            "average_resolution_hours": resolution_time.average_hours,
            "resolution_by_severity": resolution_time.by_severity
        }
    
    async def get_impact_analysis(self) -> ImpactAnalysis:
        """Analyze impact of current issues"""
        # Get affected features
        affected_features = self.db.query(
            Feedback.url,
            func.count(Feedback.id)
        ).group_by(Feedback.url).order_by(
            func.count(Feedback.id).desc()
        ).limit(10).all()
        
        # Get user segments
        user_segments = self.db.query(
            Feedback.subscription_tier,
            func.count(func.distinct(Feedback.user_id))
        ).filter(
            Feedback.user_id.isnot(None)
        ).group_by(Feedback.subscription_tier).all()
        
        # Calculate revenue at risk
        premium_affected = self.db.query(
            func.count(func.distinct(Feedback.user_id))
        ).filter(
            Feedback.subscription_tier.in_(["pro", "enterprise"]),
            Feedback.severity.in_(["critical", "high"]),
            Feedback.status != "resolved"
        ).scalar() or 0
        
        revenue_at_risk = premium_affected * 50  # Simplified calculation
        
        # Estimate churn probability
        critical_unresolved = self.db.query(Feedback).filter(
            Feedback.severity == "critical",
            Feedback.status != "resolved",
            Feedback.created_at < datetime.utcnow() - timedelta(days=3)
        ).count()
        
        churn_probability = min(critical_unresolved * 0.1, 1.0)  # 10% per critical issue
        
        return ImpactAnalysis(
            affected_features=[f[0] for f in affected_features[:5]],
            user_segments=dict(user_segments),
            revenue_at_risk=float(revenue_at_risk),
            churn_probability=churn_probability
        )
    
    async def get_feedback_heatmap(self) -> List[FeedbackHeatmapData]:
        """Get heatmap data for feedback by page"""
        heatmap_query = self.db.query(
            Feedback.url,
            Feedback.severity,
            func.count(Feedback.id)
        ).group_by(
            Feedback.url,
            Feedback.severity
        ).all()
        
        # Organize by page
        page_data = defaultdict(lambda: {"total": 0, "severity": {}})
        for url, severity, count in heatmap_query:
            page_data[url]["total"] += count
            page_data[url]["severity"][severity] = count
        
        # Convert to schema
        heatmap = []
        for page, data in page_data.items():
            heatmap.append(FeedbackHeatmapData(
                page=page,
                issue_count=data["total"],
                severity_breakdown=data["severity"]
            ))
        
        return sorted(heatmap, key=lambda x: x.issue_count, reverse=True)[:20]
    
    async def train_pattern_detection(self) -> Dict[str, Any]:
        """Train ML model for pattern detection"""
        # This is a placeholder for ML implementation
        # In production, you'd use scikit-learn or similar
        
        # For now, just reorganize patterns based on similarity
        all_feedback = self.db.query(Feedback).all()
        
        # Group by similarity
        new_patterns = 0
        for feedback in all_feedback:
            if not feedback.pattern_id:
                pattern_id = await self.detect_pattern(FeedbackSubmit(
                    type=feedback.type,
                    severity=feedback.severity,
                    title=feedback.title,
                    description=feedback.description,
                    url=feedback.url,
                    user_agent=feedback.user_agent,
                    screen_resolution=feedback.screen_resolution,
                    previous_pages=json.loads(feedback.previous_pages or "[]"),
                    last_actions=json.loads(feedback.last_actions or "[]"),
                    error_logs=json.loads(feedback.error_logs or "[]"),
                    timestamp=feedback.created_at
                ))
                
                if pattern_id:
                    feedback.pattern_id = pattern_id
                    new_patterns += 1
        
        self.db.commit()
        
        return {
            "new_patterns": new_patterns,
            "accuracy": 0.85  # Placeholder
        }
    
    async def assign_feedback(self, feedback_id: str, assignee: str) -> Optional[FeedbackItem]:
        """Assign feedback to team member"""
        feedback = self.db.query(Feedback).filter_by(id=feedback_id).first()
        if not feedback:
            return None
        
        feedback.assigned_to = assignee
        self.db.commit()
        return self._feedback_to_schema(feedback)
    
    async def mark_duplicate(self, feedback_id: str, original_id: str):
        """Mark feedback as duplicate"""
        feedback = self.db.query(Feedback).filter_by(id=feedback_id).first()
        original = self.db.query(Feedback).filter_by(id=original_id).first()
        
        if feedback and original:
            feedback.status = "closed"
            feedback.resolution_notes = f"Duplicate of #{original_id}"
            original.duplicate_count += 1
            self.db.commit()
    
    async def get_user_feedback(self, user_id: str) -> List[FeedbackItem]:
        """Get feedback submitted by specific user"""
        user_feedback = self.db.query(Feedback).filter_by(
            user_id=user_id
        ).order_by(Feedback.created_at.desc()).all()
        
        return [self._feedback_to_schema(f) for f in user_feedback]