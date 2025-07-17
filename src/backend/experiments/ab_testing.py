"""
A/B Testing framework for TradeSense.
Provides experiment management, variant assignment, and statistical analysis.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import random
import json
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats

from models.user import User
from core.config import settings
from analytics import track_experiment_event


class ExperimentStatus(str, Enum):
    """Experiment lifecycle states."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantAssignmentMethod(str, Enum):
    """Methods for assigning users to variants."""
    RANDOM = "random"
    DETERMINISTIC = "deterministic"
    STICKY = "sticky"
    COHORT_BASED = "cohort_based"


class MetricType(str, Enum):
    """Types of metrics tracked in experiments."""
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    CUSTOM = "custom"


@dataclass
class Variant:
    """Represents a variant in an experiment."""
    id: str
    name: str
    description: str
    weight: float  # Percentage of traffic (0-1)
    config: Dict[str, Any]  # Variant-specific configuration
    is_control: bool = False


@dataclass
class Metric:
    """Defines a metric to track in an experiment."""
    id: str
    name: str
    type: MetricType
    description: str
    event_name: Optional[str] = None  # Event to track for this metric
    success_criteria: Optional[Dict[str, Any]] = None
    
    def is_primary(self) -> bool:
        """Check if this is the primary metric."""
        return self.success_criteria and self.success_criteria.get('is_primary', False)


@dataclass
class ExperimentResult:
    """Results of an experiment analysis."""
    variant_id: str
    metric_id: str
    sample_size: int
    conversions: int
    conversion_rate: float
    confidence_interval: Tuple[float, float]
    p_value: Optional[float] = None
    is_significant: Optional[bool] = None
    lift: Optional[float] = None


class Experiment:
    """Represents an A/B test experiment."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        hypothesis: str,
        variants: List[Variant],
        metrics: List[Metric],
        targeting_rules: Optional[Dict[str, Any]] = None,
        assignment_method: VariantAssignmentMethod = VariantAssignmentMethod.DETERMINISTIC,
        min_sample_size: int = 1000,
        max_duration_days: int = 30,
        status: ExperimentStatus = ExperimentStatus.DRAFT
    ):
        self.id = id
        self.name = name
        self.description = description
        self.hypothesis = hypothesis
        self.variants = variants
        self.metrics = metrics
        self.targeting_rules = targeting_rules or {}
        self.assignment_method = assignment_method
        self.min_sample_size = min_sample_size
        self.max_duration_days = max_duration_days
        self.status = status
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        
        # Validate variants
        self._validate_variants()
    
    def _validate_variants(self):
        """Ensure variants are properly configured."""
        total_weight = sum(v.weight for v in self.variants)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")
        
        control_count = sum(1 for v in self.variants if v.is_control)
        if control_count != 1:
            raise ValueError(f"Exactly one control variant required, got {control_count}")
    
    def is_eligible(self, user: User, user_attributes: Dict[str, Any]) -> bool:
        """Check if user is eligible for this experiment."""
        if self.status != ExperimentStatus.RUNNING:
            return False
        
        # Apply targeting rules
        for rule_type, rule_config in self.targeting_rules.items():
            if not self._evaluate_targeting_rule(user, user_attributes, rule_type, rule_config):
                return False
        
        return True
    
    def _evaluate_targeting_rule(
        self,
        user: User,
        attributes: Dict[str, Any],
        rule_type: str,
        rule_config: Dict[str, Any]
    ) -> bool:
        """Evaluate a single targeting rule."""
        if rule_type == "new_users_only":
            account_age = (datetime.utcnow() - user.created_at).days
            return account_age <= rule_config.get("max_days", 7)
        
        elif rule_type == "subscription_tier":
            allowed_tiers = rule_config.get("tiers", [])
            return user.subscription_tier in allowed_tiers
        
        elif rule_type == "percentage_rollout":
            percentage = rule_config.get("percentage", 100)
            user_hash = int(hashlib.md5(f"{user.id}".encode()).hexdigest(), 16)
            return (user_hash % 100) < percentage
        
        elif rule_type == "custom_attribute":
            attr_name = rule_config.get("attribute")
            expected_value = rule_config.get("value")
            return attributes.get(attr_name) == expected_value
        
        return True
    
    def assign_variant(self, user: User) -> Variant:
        """Assign user to a variant."""
        if self.assignment_method == VariantAssignmentMethod.RANDOM:
            return self._random_assignment()
        
        elif self.assignment_method == VariantAssignmentMethod.DETERMINISTIC:
            return self._deterministic_assignment(user)
        
        elif self.assignment_method == VariantAssignmentMethod.STICKY:
            # In production, check database for existing assignment
            return self._deterministic_assignment(user)
        
        else:
            return self._deterministic_assignment(user)
    
    def _random_assignment(self) -> Variant:
        """Randomly assign to variant based on weights."""
        rand = random.random()
        cumulative = 0.0
        
        for variant in self.variants:
            cumulative += variant.weight
            if rand < cumulative:
                return variant
        
        return self.variants[-1]  # Fallback
    
    def _deterministic_assignment(self, user: User) -> Variant:
        """Deterministically assign based on user ID."""
        # Hash user ID with experiment ID for consistent assignment
        hash_input = f"{self.id}:{user.id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 1000) / 1000.0
        
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight
            if bucket < cumulative:
                return variant
        
        return self.variants[-1]  # Fallback
    
    def get_control_variant(self) -> Variant:
        """Get the control variant."""
        for variant in self.variants:
            if variant.is_control:
                return variant
        raise ValueError("No control variant found")
    
    def get_primary_metric(self) -> Optional[Metric]:
        """Get the primary success metric."""
        for metric in self.metrics:
            if metric.is_primary():
                return metric
        return self.metrics[0] if self.metrics else None


class ABTestingService:
    """Main service for managing A/B tests."""
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {exp_id: variant_id}
        self.results_cache: Dict[str, List[ExperimentResult]] = {}
    
    def create_experiment(self, experiment: Experiment) -> str:
        """Create a new experiment."""
        if experiment.id in self.experiments:
            raise ValueError(f"Experiment {experiment.id} already exists")
        
        self.experiments[experiment.id] = experiment
        return experiment.id
    
    def start_experiment(self, experiment_id: str):
        """Start running an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Can only start experiments in DRAFT status")
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
    
    def stop_experiment(self, experiment_id: str, reason: str = ""):
        """Stop a running experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.utcnow()
    
    async def get_variant(
        self,
        user: User,
        experiment_id: str,
        user_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[Variant]:
        """Get variant assignment for user."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        
        # Check eligibility
        if not experiment.is_eligible(user, user_attributes or {}):
            return None
        
        # Check for existing assignment
        user_assignments = self.assignments.get(str(user.id), {})
        if experiment_id in user_assignments:
            variant_id = user_assignments[experiment_id]
            for variant in experiment.variants:
                if variant.id == variant_id:
                    return variant
        
        # Assign new variant
        variant = experiment.assign_variant(user)
        
        # Store assignment
        if str(user.id) not in self.assignments:
            self.assignments[str(user.id)] = {}
        self.assignments[str(user.id)][experiment_id] = variant.id
        
        # Track assignment event
        await track_experiment_event(
            user_id=str(user.id),
            experiment_id=experiment_id,
            event_type="assignment",
            variant_id=variant.id
        )
        
        return variant
    
    async def track_conversion(
        self,
        user_id: str,
        experiment_id: str,
        metric_id: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a conversion event for an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        # Get user's variant
        user_assignments = self.assignments.get(user_id, {})
        variant_id = user_assignments.get(experiment_id)
        if not variant_id:
            return
        
        # Track conversion event
        await track_experiment_event(
            user_id=user_id,
            experiment_id=experiment_id,
            event_type="conversion",
            variant_id=variant_id,
            metric_id=metric_id,
            value=value,
            metadata=metadata
        )
    
    def analyze_experiment(
        self,
        experiment_id: str,
        metric_id: str,
        confidence_level: float = 0.95
    ) -> List[ExperimentResult]:
        """Analyze experiment results for a specific metric."""
        # In production, this would query the database
        # For now, return mock results
        
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return []
        
        results = []
        control_result = None
        
        for variant in experiment.variants:
            # Mock data - in production, aggregate from events
            sample_size = random.randint(500, 2000)
            conversions = int(sample_size * random.uniform(0.05, 0.25))
            conversion_rate = conversions / sample_size
            
            # Calculate confidence interval
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            margin_of_error = z_score * np.sqrt(
                (conversion_rate * (1 - conversion_rate)) / sample_size
            )
            ci_lower = max(0, conversion_rate - margin_of_error)
            ci_upper = min(1, conversion_rate + margin_of_error)
            
            result = ExperimentResult(
                variant_id=variant.id,
                metric_id=metric_id,
                sample_size=sample_size,
                conversions=conversions,
                conversion_rate=conversion_rate,
                confidence_interval=(ci_lower, ci_upper)
            )
            
            if variant.is_control:
                control_result = result
            
            results.append(result)
        
        # Calculate statistical significance vs control
        if control_result:
            for result in results:
                if result.variant_id != control_result.variant_id:
                    # Chi-square test
                    observed = np.array([
                        [result.conversions, result.sample_size - result.conversions],
                        [control_result.conversions, control_result.sample_size - control_result.conversions]
                    ])
                    chi2, p_value = stats.chi2_contingency(observed)[:2]
                    
                    result.p_value = p_value
                    result.is_significant = p_value < (1 - confidence_level)
                    result.lift = (
                        (result.conversion_rate - control_result.conversion_rate) 
                        / control_result.conversion_rate
                    ) if control_result.conversion_rate > 0 else 0
        
        return results
    
    def get_winning_variant(
        self,
        experiment_id: str,
        metric_id: str,
        min_improvement: float = 0.05
    ) -> Optional[str]:
        """Determine if there's a statistically significant winner."""
        results = self.analyze_experiment(experiment_id, metric_id)
        
        control_result = None
        best_variant = None
        best_lift = 0
        
        for result in results:
            variant = next(
                v for v in self.experiments[experiment_id].variants 
                if v.id == result.variant_id
            )
            
            if variant.is_control:
                control_result = result
                continue
            
            if result.is_significant and result.lift > min_improvement:
                if result.lift > best_lift:
                    best_lift = result.lift
                    best_variant = result.variant_id
        
        return best_variant
    
    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8,
        significance_level: float = 0.05
    ) -> int:
        """Calculate required sample size for experiment."""
        # Using formula for two-proportion z-test
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        pooled_prob = (p1 + p2) / 2
        
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        z_beta = stats.norm.ppf(power)
        
        numerator = (z_alpha + z_beta) ** 2
        denominator = (p1 - p2) ** 2
        
        n = numerator * (p1 * (1 - p1) + p2 * (1 - p2)) / denominator
        
        return int(np.ceil(n))
    
    def estimate_experiment_duration(
        self,
        experiment_id: str,
        daily_traffic: int
    ) -> int:
        """Estimate how many days experiment needs to run."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return 0
        
        # Account for targeting rules reducing eligible traffic
        eligibility_rate = 1.0
        if "percentage_rollout" in experiment.targeting_rules:
            eligibility_rate *= experiment.targeting_rules["percentage_rollout"].get("percentage", 100) / 100
        
        eligible_daily_traffic = int(daily_traffic * eligibility_rate)
        
        # Calculate based on minimum sample size per variant
        min_sample_per_variant = experiment.min_sample_size
        days_needed = min_sample_per_variant / (eligible_daily_traffic * min(v.weight for v in experiment.variants))
        
        return min(int(np.ceil(days_needed)), experiment.max_duration_days)


# Example experiments
class ExperimentLibrary:
    """Pre-defined experiments for common use cases."""
    
    @staticmethod
    def pricing_page_experiment() -> Experiment:
        """Test different pricing page layouts."""
        return Experiment(
            id="pricing_page_v2",
            name="Pricing Page Redesign",
            description="Test new pricing page layout with clearer value props",
            hypothesis="Clearer value propositions will increase pro tier conversions by 15%",
            variants=[
                Variant(
                    id="control",
                    name="Current Pricing Page",
                    description="Existing pricing page layout",
                    weight=0.5,
                    config={},
                    is_control=True
                ),
                Variant(
                    id="clear_value_props",
                    name="Clear Value Props",
                    description="Pricing page with bullet points for each tier",
                    weight=0.5,
                    config={
                        "show_value_bullets": True,
                        "highlight_savings": True
                    }
                )
            ],
            metrics=[
                Metric(
                    id="pro_conversion",
                    name="Pro Tier Conversion Rate",
                    type=MetricType.CONVERSION,
                    description="Percentage of visitors who upgrade to Pro",
                    event_name="subscription_started",
                    success_criteria={"is_primary": True, "min_improvement": 0.15}
                ),
                Metric(
                    id="page_engagement",
                    name="Pricing Page Engagement",
                    type=MetricType.ENGAGEMENT,
                    description="Time spent on pricing page",
                    event_name="page_view_duration"
                )
            ],
            targeting_rules={
                "subscription_tier": {"tiers": ["free"]}
            },
            min_sample_size=1000
        )
    
    @staticmethod
    def onboarding_flow_experiment() -> Experiment:
        """Test different onboarding flows."""
        return Experiment(
            id="onboarding_flow_v3",
            name="Streamlined Onboarding",
            description="Test removing optional steps from onboarding",
            hypothesis="Shorter onboarding will increase completion rate by 20%",
            variants=[
                Variant(
                    id="control",
                    name="Full Onboarding",
                    description="All onboarding steps including optional ones",
                    weight=0.5,
                    config={"steps": ["welcome", "connect_broker", "preferences", "goals", "first_trade"]},
                    is_control=True
                ),
                Variant(
                    id="streamlined",
                    name="Streamlined Onboarding",
                    description="Only essential onboarding steps",
                    weight=0.5,
                    config={"steps": ["welcome", "connect_broker", "first_trade"]}
                )
            ],
            metrics=[
                Metric(
                    id="completion_rate",
                    name="Onboarding Completion Rate",
                    type=MetricType.CONVERSION,
                    description="Percentage who complete onboarding",
                    event_name="onboarding_completed",
                    success_criteria={"is_primary": True, "min_improvement": 0.20}
                ),
                Metric(
                    id="time_to_complete",
                    name="Time to Complete",
                    type=MetricType.ENGAGEMENT,
                    description="Average time to complete onboarding"
                ),
                Metric(
                    id="day7_retention",
                    name="7-Day Retention",
                    type=MetricType.RETENTION,
                    description="Users active after 7 days"
                )
            ],
            targeting_rules={
                "new_users_only": {"max_days": 1}
            },
            assignment_method=VariantAssignmentMethod.STICKY,
            min_sample_size=500
        )
    
    @staticmethod
    def email_frequency_experiment() -> Experiment:
        """Test different email frequencies."""
        return Experiment(
            id="email_frequency_test",
            name="Optimal Email Frequency",
            description="Find the right balance of email communications",
            hypothesis="Weekly digest emails will improve engagement without increasing unsubscribes",
            variants=[
                Variant(
                    id="control",
                    name="Daily Emails",
                    description="Current daily email schedule",
                    weight=0.33,
                    config={"frequency": "daily"},
                    is_control=True
                ),
                Variant(
                    id="weekly",
                    name="Weekly Digest",
                    description="Weekly summary emails",
                    weight=0.33,
                    config={"frequency": "weekly"}
                ),
                Variant(
                    id="biweekly",
                    name="Bi-weekly Updates",
                    description="Emails every two weeks",
                    weight=0.34,
                    config={"frequency": "biweekly"}
                )
            ],
            metrics=[
                Metric(
                    id="email_engagement",
                    name="Email Open Rate",
                    type=MetricType.ENGAGEMENT,
                    description="Percentage of emails opened",
                    success_criteria={"is_primary": True}
                ),
                Metric(
                    id="unsubscribe_rate",
                    name="Unsubscribe Rate",
                    type=MetricType.CONVERSION,
                    description="Percentage who unsubscribe"
                ),
                Metric(
                    id="app_engagement",
                    name="App Engagement",
                    type=MetricType.ENGAGEMENT,
                    description="App usage after email"
                )
            ],
            targeting_rules={
                "percentage_rollout": {"percentage": 30}
            },
            min_sample_size=2000
        )


# Initialize service
ab_testing_service = ABTestingService()