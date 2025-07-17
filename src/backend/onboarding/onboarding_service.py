"""
User onboarding service for TradeSense.
Manages the new user experience and progressive feature introduction.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.email_service import email_service
from src.backend.analytics import track_onboarding_event
from src.backend.features.feature_flags import feature_flag_service


class OnboardingStep(str, Enum):
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    TRADING_PREFERENCES = "trading_preferences"
    FIRST_TRADE = "first_trade"
    ANALYTICS_TOUR = "analytics_tour"
    PLAN_SELECTION = "plan_selection"
    COMPLETED = "completed"


class OnboardingService:
    """Manages user onboarding process."""
    
    def __init__(self):
        self.steps = [
            {
                "id": OnboardingStep.WELCOME,
                "title": "Welcome to TradeSense",
                "description": "Get started with your trading analytics journey",
                "required": True,
                "order": 1
            },
            {
                "id": OnboardingStep.PROFILE_SETUP,
                "title": "Complete Your Profile",
                "description": "Tell us about your trading experience",
                "required": True,
                "order": 2
            },
            {
                "id": OnboardingStep.TRADING_PREFERENCES,
                "title": "Set Trading Preferences",
                "description": "Customize your trading setup",
                "required": False,
                "order": 3
            },
            {
                "id": OnboardingStep.FIRST_TRADE,
                "title": "Import Your First Trade",
                "description": "Add trades manually or import from CSV",
                "required": True,
                "order": 4
            },
            {
                "id": OnboardingStep.ANALYTICS_TOUR,
                "title": "Explore Analytics",
                "description": "Learn about your analytics dashboard",
                "required": False,
                "order": 5
            },
            {
                "id": OnboardingStep.PLAN_SELECTION,
                "title": "Choose Your Plan",
                "description": "Select the plan that fits your needs",
                "required": False,
                "order": 6
            }
        ]
        
        # Onboarding tips shown progressively
        self.tips = {
            "day_1": [
                {
                    "id": "import_trades",
                    "title": "Import Your Trades",
                    "content": "You can import trades from CSV or connect to your broker",
                    "link": "/trades/import"
                },
                {
                    "id": "basic_analytics",
                    "title": "View Your Performance",
                    "content": "Check your win rate and P&L in the Analytics dashboard",
                    "link": "/analytics"
                }
            ],
            "day_3": [
                {
                    "id": "set_goals",
                    "title": "Set Trading Goals",
                    "content": "Define your trading objectives and track progress",
                    "link": "/settings/goals"
                },
                {
                    "id": "journal_entry",
                    "title": "Start Journaling",
                    "content": "Document your trades and thoughts for better insights",
                    "link": "/journal"
                }
            ],
            "day_7": [
                {
                    "id": "advanced_analytics",
                    "title": "Explore Advanced Analytics",
                    "content": "Dive deeper into your trading patterns and performance",
                    "link": "/analytics/advanced"
                },
                {
                    "id": "upgrade_prompt",
                    "title": "Unlock More Features",
                    "content": "Upgrade to Pro for unlimited trades and advanced features",
                    "link": "/subscription"
                }
            ]
        }
    
    async def get_user_onboarding_state(
        self,
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get current onboarding state for user."""
        
        # Get onboarding progress
        result = await db.execute(
            text("""
                SELECT 
                    onboarding_step,
                    onboarding_completed_at,
                    onboarding_data
                FROM user_onboarding
                WHERE user_id = :user_id
            """),
            {"user_id": user.id}
        )
        
        onboarding_data = result.first()
        
        if not onboarding_data:
            # Initialize onboarding for new user
            await self._initialize_onboarding(user, db)
            current_step = OnboardingStep.WELCOME
            completed_steps = []
            data = {}
        else:
            current_step = onboarding_data.onboarding_step
            data = json.loads(onboarding_data.onboarding_data) if onboarding_data.onboarding_data else {}
            completed_steps = data.get("completed_steps", [])
        
        # Get user stats for conditional steps
        stats = await self._get_user_stats(user, db)
        
        # Determine next steps
        next_steps = self._get_next_steps(current_step, completed_steps, stats)
        
        # Get relevant tips based on account age
        account_age = (datetime.utcnow() - user.created_at).days
        current_tips = self._get_tips_for_day(account_age)
        
        return {
            "current_step": current_step,
            "completed_steps": completed_steps,
            "next_steps": next_steps,
            "progress_percentage": self._calculate_progress(completed_steps),
            "is_completed": current_step == OnboardingStep.COMPLETED,
            "tips": current_tips,
            "user_stats": stats,
            "show_checklist": len(completed_steps) < len(self.steps) - 1  # -1 for COMPLETED
        }
    
    async def complete_step(
        self,
        user: User,
        step: OnboardingStep,
        step_data: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Mark an onboarding step as completed."""
        
        # Get current onboarding data
        result = await db.execute(
            text("""
                SELECT onboarding_data
                FROM user_onboarding
                WHERE user_id = :user_id
            """),
            {"user_id": user.id}
        )
        
        row = result.first()
        if row and row.onboarding_data:
            data = json.loads(row.onboarding_data)
        else:
            data = {}
        
        # Update completed steps
        completed_steps = data.get("completed_steps", [])
        if step not in completed_steps:
            completed_steps.append(step)
        
        # Store step-specific data
        if step_data:
            step_history = data.get("step_history", {})
            step_history[step] = {
                "completed_at": datetime.utcnow().isoformat(),
                "data": step_data
            }
            data["step_history"] = step_history
        
        data["completed_steps"] = completed_steps
        
        # Determine next step
        next_step = self._get_next_required_step(completed_steps)
        
        # Update database
        if next_step == OnboardingStep.COMPLETED:
            # Onboarding completed
            await db.execute(
                text("""
                    UPDATE user_onboarding
                    SET onboarding_step = :step,
                        onboarding_data = :data,
                        onboarding_completed_at = NOW(),
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """),
                {
                    "user_id": user.id,
                    "step": OnboardingStep.COMPLETED,
                    "data": json.dumps(data)
                }
            )
            
            # Send completion email
            await self._send_completion_email(user)
            
            # Track completion
            await track_onboarding_event(
                user_id=str(user.id),
                event="onboarding_completed",
                data={"total_steps": len(completed_steps)}
            )
        else:
            # Update to next step
            await db.execute(
                text("""
                    UPDATE user_onboarding
                    SET onboarding_step = :step,
                        onboarding_data = :data,
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """),
                {
                    "user_id": user.id,
                    "step": next_step,
                    "data": json.dumps(data)
                }
            )
        
        await db.commit()
        
        # Track step completion
        await track_onboarding_event(
            user_id=str(user.id),
            event=f"completed_step_{step}",
            data=step_data
        )
        
        return {
            "success": True,
            "next_step": next_step,
            "is_completed": next_step == OnboardingStep.COMPLETED,
            "progress_percentage": self._calculate_progress(completed_steps)
        }
    
    async def skip_step(
        self,
        user: User,
        step: OnboardingStep,
        reason: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Skip an optional onboarding step."""
        
        # Check if step is skippable
        step_config = next((s for s in self.steps if s["id"] == step), None)
        if not step_config or step_config["required"]:
            return {
                "success": False,
                "error": "Cannot skip required step"
            }
        
        # Mark as skipped
        step_data = {
            "skipped": True,
            "reason": reason
        }
        
        return await self.complete_step(user, step, step_data, db)
    
    async def get_onboarding_checklist(
        self,
        user: User,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get onboarding checklist with status."""
        
        state = await self.get_user_onboarding_state(user, db)
        completed_steps = state["completed_steps"]
        
        checklist = []
        for step in self.steps:
            if step["id"] == OnboardingStep.COMPLETED:
                continue
                
            checklist.append({
                "id": step["id"],
                "title": step["title"],
                "description": step["description"],
                "required": step["required"],
                "completed": step["id"] in completed_steps,
                "order": step["order"]
            })
        
        return sorted(checklist, key=lambda x: x["order"])
    
    async def send_onboarding_email(
        self,
        user: User,
        email_type: str
    ):
        """Send onboarding-related emails."""
        
        if email_type == "welcome":
            await email_service.send_welcome_email(
                email=user.email,
                name=user.full_name,
                verification_link=f"https://app.tradesense.com/verify?token={user.verification_token}"
            )
        
        elif email_type == "day_3_tips":
            await email_service.send_email(
                to_email=user.email,
                subject="🎯 Pro Tips for TradeSense",
                body=self._get_tips_email_content(user, 3)
            )
        
        elif email_type == "day_7_checkin":
            await email_service.send_email(
                to_email=user.email,
                subject="📊 How's your trading journey going?",
                body=self._get_checkin_email_content(user, 7)
            )
    
    # Helper methods
    async def _initialize_onboarding(
        self,
        user: User,
        db: AsyncSession
    ):
        """Initialize onboarding for new user."""
        
        await db.execute(
            text("""
                INSERT INTO user_onboarding (
                    user_id, onboarding_step, onboarding_data
                ) VALUES (
                    :user_id, :step, :data
                )
                ON CONFLICT (user_id) DO NOTHING
            """),
            {
                "user_id": user.id,
                "step": OnboardingStep.WELCOME,
                "data": json.dumps({
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_steps": []
                })
            }
        )
        
        await db.commit()
    
    async def _get_user_stats(
        self,
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get user statistics for onboarding logic."""
        
        # Get trade count
        trade_result = await db.execute(
            text("""
                SELECT COUNT(*) as trade_count
                FROM trades
                WHERE user_id = :user_id
            """),
            {"user_id": user.id}
        )
        trade_count = trade_result.scalar() or 0
        
        # Get profile completion
        profile_complete = all([
            user.full_name,
            user.email_verified if hasattr(user, "email_verified") else True
        ])
        
        return {
            "trade_count": trade_count,
            "profile_complete": profile_complete,
            "account_age_days": (datetime.utcnow() - user.created_at).days,
            "has_subscription": user.subscription_tier != "free"
        }
    
    def _get_next_steps(
        self,
        current_step: str,
        completed_steps: List[str],
        user_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get next recommended steps."""
        
        next_steps = []
        
        for step in self.steps:
            if step["id"] in completed_steps or step["id"] == OnboardingStep.COMPLETED:
                continue
            
            # Check prerequisites
            if step["id"] == OnboardingStep.FIRST_TRADE and user_stats["trade_count"] > 0:
                # Auto-complete if user already has trades
                completed_steps.append(step["id"])
                continue
            
            if step["id"] == OnboardingStep.PLAN_SELECTION and user_stats["has_subscription"]:
                # Skip if already subscribed
                completed_steps.append(step["id"])
                continue
            
            next_steps.append({
                "id": step["id"],
                "title": step["title"],
                "description": step["description"],
                "required": step["required"]
            })
            
            # Return top 3 next steps
            if len(next_steps) >= 3:
                break
        
        return next_steps
    
    def _get_next_required_step(
        self,
        completed_steps: List[str]
    ) -> str:
        """Get next required step or COMPLETED."""
        
        for step in self.steps:
            if step["required"] and step["id"] not in completed_steps:
                return step["id"]
        
        return OnboardingStep.COMPLETED
    
    def _calculate_progress(
        self,
        completed_steps: List[str]
    ) -> int:
        """Calculate onboarding progress percentage."""
        
        # Count only non-COMPLETED steps
        total_steps = len([s for s in self.steps if s["id"] != OnboardingStep.COMPLETED])
        if total_steps == 0:
            return 100
        
        return int((len(completed_steps) / total_steps) * 100)
    
    def _get_tips_for_day(
        self,
        account_age_days: int
    ) -> List[Dict[str, Any]]:
        """Get relevant tips based on account age."""
        
        if account_age_days <= 1:
            return self.tips.get("day_1", [])
        elif account_age_days <= 3:
            return self.tips.get("day_3", [])
        elif account_age_days <= 7:
            return self.tips.get("day_7", [])
        else:
            # Return a mix of advanced tips
            return []
    
    async def _send_completion_email(self, user: User):
        """Send onboarding completion email."""
        
        await email_service.send_email(
            to_email=user.email,
            subject="🎉 Welcome to TradeSense - You're All Set!",
            body=f"""Hi {user.full_name},

Congratulations on completing your TradeSense setup! You're now ready to take your trading to the next level.

Here's what you can do next:
- Import more trades to build your history
- Explore advanced analytics features
- Set up automated reports
- Join our community forum

If you have any questions, our support team is here to help.

Happy trading!
The TradeSense Team"""
        )
    
    def _get_tips_email_content(self, user: User, day: int) -> str:
        """Generate tips email content."""
        
        tips = self.tips.get(f"day_{day}", [])
        tips_html = "\n".join([
            f"<li><strong>{tip['title']}</strong>: {tip['content']}</li>"
            for tip in tips
        ])
        
        return f"""Hi {user.full_name},

You've been using TradeSense for {day} days! Here are some tips to help you get more value:

<ul>
{tips_html}
</ul>

Visit your dashboard to explore these features: https://app.tradesense.com

Best regards,
The TradeSense Team"""
    
    def _get_checkin_email_content(self, user: User, day: int) -> str:
        """Generate check-in email content."""
        
        return f"""Hi {user.full_name},

It's been a week since you joined TradeSense! How's your trading journey going?

Quick wins to try this week:
- Review your win/loss ratio in Analytics
- Set a weekly trading goal
- Try our risk analysis tools
- Export your first performance report

Need help? Reply to this email or visit our support center.

Keep up the great work!
The TradeSense Team"""


# Initialize onboarding service
onboarding_service = OnboardingService()