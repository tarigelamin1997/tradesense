"""
Feature flags system for TradeSense.
Enables controlled feature rollouts and A/B testing.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session import get_db
from models.user import User
from analytics import track_feature_usage


class FeatureFlagType(str, Enum):
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    VARIANT = "variant"


class FeatureFlagStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"


class TargetingRule:
    """Defines targeting criteria for feature flags."""
    
    def __init__(self, rule_config: Dict[str, Any]):
        self.user_tiers = rule_config.get("user_tiers", [])
        self.user_ids = rule_config.get("user_ids", [])
        self.user_percentage = rule_config.get("user_percentage", 100)
        self.created_after = rule_config.get("created_after")
        self.created_before = rule_config.get("created_before")
        self.has_traded = rule_config.get("has_traded", None)
        self.min_trades = rule_config.get("min_trades", 0)
        self.custom_attributes = rule_config.get("custom_attributes", {})
    
    def matches_user(self, user: User, user_stats: Dict[str, Any]) -> bool:
        """Check if user matches targeting criteria."""
        
        # Check tier
        if self.user_tiers and user.subscription_tier not in self.user_tiers:
            return False
        
        # Check specific user IDs
        if self.user_ids and str(user.id) not in self.user_ids:
            return False
        
        # Check account age
        if self.created_after:
            created_after_date = datetime.fromisoformat(self.created_after)
            if user.created_at < created_after_date:
                return False
        
        if self.created_before:
            created_before_date = datetime.fromisoformat(self.created_before)
            if user.created_at > created_before_date:
                return False
        
        # Check trading activity
        if self.has_traded is not None:
            has_trades = user_stats.get("trade_count", 0) > 0
            if self.has_traded != has_trades:
                return False
        
        if self.min_trades > 0:
            if user_stats.get("trade_count", 0) < self.min_trades:
                return False
        
        # Check custom attributes
        for attr, expected_value in self.custom_attributes.items():
            if user_stats.get(attr) != expected_value:
                return False
        
        # Check percentage rollout
        if self.user_percentage < 100:
            # Use consistent hashing for stable assignment
            user_hash = int(hashlib.md5(str(user.id).encode()).hexdigest(), 16)
            if (user_hash % 100) >= self.user_percentage:
                return False
        
        return True


class FeatureFlag:
    """Represents a feature flag configuration."""
    
    def __init__(self, flag_data: Dict[str, Any]):
        self.id = flag_data["id"]
        self.key = flag_data["key"]
        self.name = flag_data["name"]
        self.description = flag_data.get("description", "")
        self.type = FeatureFlagType(flag_data["type"])
        self.status = FeatureFlagStatus(flag_data["status"])
        self.default_value = flag_data.get("default_value", False)
        self.variants = flag_data.get("variants", {})
        self.targeting_rules = [
            TargetingRule(rule) for rule in flag_data.get("targeting_rules", [])
        ]
        self.start_date = flag_data.get("start_date")
        self.end_date = flag_data.get("end_date")
        self.metadata = flag_data.get("metadata", {})
    
    def is_active(self) -> bool:
        """Check if flag is currently active."""
        if self.status != FeatureFlagStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        
        if self.start_date:
            start = datetime.fromisoformat(self.start_date)
            if now < start:
                return False
        
        if self.end_date:
            end = datetime.fromisoformat(self.end_date)
            if now > end:
                return False
        
        return True
    
    def evaluate(self, user: Optional[User], user_stats: Dict[str, Any]) -> Any:
        """Evaluate flag value for a user."""
        if not self.is_active():
            return self.default_value
        
        if not user:
            return self.default_value
        
        # Check if any targeting rule matches
        for rule in self.targeting_rules:
            if rule.matches_user(user, user_stats):
                return self._get_value_for_user(user)
        
        return self.default_value
    
    def _get_value_for_user(self, user: User) -> Any:
        """Get the appropriate value based on flag type."""
        if self.type == FeatureFlagType.BOOLEAN:
            return True
        
        elif self.type == FeatureFlagType.VARIANT:
            # Use consistent hashing for variant assignment
            if not self.variants:
                return self.default_value
            
            user_hash = int(hashlib.md5(
                f"{self.key}:{user.id}".encode()
            ).hexdigest(), 16)
            
            # Calculate variant based on weights
            total_weight = sum(v.get("weight", 1) for v in self.variants.values())
            position = user_hash % total_weight
            
            current_weight = 0
            for variant_key, variant_config in self.variants.items():
                current_weight += variant_config.get("weight", 1)
                if position < current_weight:
                    return variant_key
            
            return self.default_value
        
        return self.default_value


class FeatureFlagService:
    """Manages feature flags and evaluations."""
    
    def __init__(self):
        self._flags_cache: Dict[str, FeatureFlag] = {}
        self._last_cache_update = None
        self._cache_ttl = timedelta(minutes=5)
        
        # Default feature flags
        self._default_flags = {
            "new_analytics_dashboard": {
                "key": "new_analytics_dashboard",
                "name": "New Analytics Dashboard",
                "description": "Redesigned analytics dashboard with advanced visualizations",
                "type": FeatureFlagType.PERCENTAGE,
                "status": FeatureFlagStatus.ACTIVE,
                "default_value": False,
                "targeting_rules": [
                    {
                        "user_percentage": 50,
                        "user_tiers": ["pro", "premium"]
                    }
                ]
            },
            "ai_trade_insights": {
                "key": "ai_trade_insights",
                "name": "AI Trade Insights",
                "description": "AI-powered trade analysis and recommendations",
                "type": FeatureFlagType.BOOLEAN,
                "status": FeatureFlagStatus.ACTIVE,
                "default_value": False,
                "targeting_rules": [
                    {
                        "user_tiers": ["premium"]
                    }
                ]
            },
            "mobile_app_beta": {
                "key": "mobile_app_beta",
                "name": "Mobile App Beta Access",
                "description": "Early access to mobile app",
                "type": FeatureFlagType.USER_LIST,
                "status": FeatureFlagStatus.ACTIVE,
                "default_value": False,
                "targeting_rules": [
                    {
                        "user_ids": []  # Add beta tester IDs here
                    }
                ]
            },
            "export_format": {
                "key": "export_format",
                "name": "Export Format Options",
                "description": "Test different export format options",
                "type": FeatureFlagType.VARIANT,
                "status": FeatureFlagStatus.ACTIVE,
                "default_value": "csv",
                "variants": {
                    "csv": {"weight": 50},
                    "excel": {"weight": 30},
                    "json": {"weight": 20}
                }
            }
        }
    
    async def get_flag(
        self,
        flag_key: str,
        db: AsyncSession
    ) -> Optional[FeatureFlag]:
        """Get a feature flag by key."""
        
        # Check cache first
        if await self._should_refresh_cache():
            await self._refresh_cache(db)
        
        # Check database flags
        if flag_key in self._flags_cache:
            return self._flags_cache[flag_key]
        
        # Check default flags
        if flag_key in self._default_flags:
            flag_data = self._default_flags[flag_key].copy()
            flag_data["id"] = f"default_{flag_key}"
            return FeatureFlag(flag_data)
        
        return None
    
    async def evaluate_flag(
        self,
        flag_key: str,
        user: Optional[User],
        db: AsyncSession
    ) -> Any:
        """Evaluate a feature flag for a user."""
        
        flag = await self.get_flag(flag_key, db)
        if not flag:
            return None
        
        # Get user stats if user provided
        user_stats = {}
        if user:
            user_stats = await self._get_user_stats(user, db)
        
        value = flag.evaluate(user, user_stats)
        
        # Track evaluation
        if user:
            await track_feature_usage(
                user_id=str(user.id),
                event="flag_evaluated",
                flag_key=flag_key,
                value=str(value)
            )
        
        return value
    
    async def evaluate_all_flags(
        self,
        user: Optional[User],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Evaluate all flags for a user."""
        
        await self._refresh_cache(db)
        
        user_stats = {}
        if user:
            user_stats = await self._get_user_stats(user, db)
        
        results = {}
        
        # Evaluate database flags
        for flag_key, flag in self._flags_cache.items():
            results[flag_key] = flag.evaluate(user, user_stats)
        
        # Evaluate default flags
        for flag_key, flag_config in self._default_flags.items():
            if flag_key not in results:
                flag_data = flag_config.copy()
                flag_data["id"] = f"default_{flag_key}"
                flag = FeatureFlag(flag_data)
                results[flag_key] = flag.evaluate(user, user_stats)
        
        return results
    
    async def create_flag(
        self,
        key: str,
        name: str,
        description: str,
        flag_type: FeatureFlagType,
        default_value: Any,
        targeting_rules: List[Dict[str, Any]],
        variants: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: AsyncSession = None
    ) -> str:
        """Create a new feature flag."""
        
        flag_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO feature_flags (
                    id, key, name, description, type,
                    status, default_value, targeting_rules,
                    variants, start_date, end_date
                ) VALUES (
                    :id, :key, :name, :description, :type,
                    :status, :default_value, :targeting_rules,
                    :variants, :start_date, :end_date
                )
            """),
            {
                "id": flag_id,
                "key": key,
                "name": name,
                "description": description,
                "type": flag_type,
                "status": FeatureFlagStatus.ACTIVE,
                "default_value": json.dumps(default_value),
                "targeting_rules": json.dumps(targeting_rules),
                "variants": json.dumps(variants) if variants else None,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        await db.commit()
        
        # Clear cache
        self._flags_cache.clear()
        self._last_cache_update = None
        
        return flag_id
    
    async def update_flag(
        self,
        flag_id: str,
        updates: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """Update a feature flag."""
        
        # Build update query
        set_clauses = []
        params = {"flag_id": flag_id}
        
        for field, value in updates.items():
            if field in ["name", "description", "status", "type"]:
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
            elif field in ["default_value", "targeting_rules", "variants"]:
                set_clauses.append(f"{field} = :{field}")
                params[field] = json.dumps(value)
            elif field in ["start_date", "end_date"]:
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = NOW()")
        
        await db.execute(
            text(f"""
                UPDATE feature_flags
                SET {', '.join(set_clauses)}
                WHERE id = :flag_id
            """),
            params
        )
        
        await db.commit()
        
        # Clear cache
        self._flags_cache.clear()
        self._last_cache_update = None
        
        return True
    
    async def get_all_flags(
        self,
        include_inactive: bool = False,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get all feature flags."""
        
        where_clause = "" if include_inactive else "WHERE status = 'active'"
        
        result = await db.execute(
            text(f"""
                SELECT 
                    id, key, name, description, type,
                    status, default_value, targeting_rules,
                    variants, start_date, end_date,
                    created_at, updated_at
                FROM feature_flags
                {where_clause}
                ORDER BY name
            """)
        )
        
        flags = []
        for row in result:
            flags.append({
                "id": str(row.id),
                "key": row.key,
                "name": row.name,
                "description": row.description,
                "type": row.type,
                "status": row.status,
                "default_value": json.loads(row.default_value) if row.default_value else None,
                "targeting_rules": json.loads(row.targeting_rules) if row.targeting_rules else [],
                "variants": json.loads(row.variants) if row.variants else {},
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        # Add default flags if not overridden
        db_keys = {f["key"] for f in flags}
        for key, config in self._default_flags.items():
            if key not in db_keys:
                flag_data = config.copy()
                flag_data["id"] = f"default_{key}"
                flag_data["created_at"] = None
                flag_data["updated_at"] = None
                flags.append(flag_data)
        
        return flags
    
    # Helper methods
    async def _should_refresh_cache(self) -> bool:
        """Check if cache needs refreshing."""
        if not self._last_cache_update:
            return True
        
        return datetime.utcnow() - self._last_cache_update > self._cache_ttl
    
    async def _refresh_cache(self, db: AsyncSession):
        """Refresh the flags cache from database."""
        
        result = await db.execute(
            text("""
                SELECT 
                    id, key, name, description, type,
                    status, default_value, targeting_rules,
                    variants, start_date, end_date, metadata
                FROM feature_flags
                WHERE status = 'active'
            """)
        )
        
        self._flags_cache.clear()
        
        for row in result:
            flag_data = {
                "id": str(row.id),
                "key": row.key,
                "name": row.name,
                "description": row.description,
                "type": row.type,
                "status": row.status,
                "default_value": json.loads(row.default_value) if row.default_value else None,
                "targeting_rules": json.loads(row.targeting_rules) if row.targeting_rules else [],
                "variants": json.loads(row.variants) if row.variants else {},
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "metadata": json.loads(row.metadata) if row.metadata else {}
            }
            
            self._flags_cache[row.key] = FeatureFlag(flag_data)
        
        self._last_cache_update = datetime.utcnow()
    
    async def _get_user_stats(
        self,
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get user statistics for targeting evaluation."""
        
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
        
        # Get last activity
        activity_result = await db.execute(
            text("""
                SELECT MAX(created_at) as last_trade_date
                FROM trades
                WHERE user_id = :user_id
            """),
            {"user_id": user.id}
        )
        last_trade_date = activity_result.scalar()
        
        return {
            "trade_count": trade_count,
            "last_trade_date": last_trade_date,
            "account_age_days": (datetime.utcnow() - user.created_at).days,
            "has_api_key": bool(user.api_key) if hasattr(user, "api_key") else False,
            "email_verified": user.email_verified if hasattr(user, "email_verified") else True
        }


# Initialize feature flag service
import uuid
feature_flag_service = FeatureFlagService()