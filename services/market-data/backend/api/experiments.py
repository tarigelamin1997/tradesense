"""
A/B Testing API endpoints for TradeSense.
Manages experiments and variant assignments.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from api.deps import get_current_user
from models.user import User
from experiments.ab_testing import (
    ab_testing_service,
    Experiment,
    Variant,
    Metric,
    ExperimentStatus,
    VariantAssignmentMethod,
    MetricType,
    ExperimentLibrary
)
from api.admin import require_admin

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


# Request/Response models
class VariantConfig(BaseModel):
    id: str
    name: str
    description: str
    weight: float = Field(gt=0, le=1)
    config: Dict[str, Any] = {}
    is_control: bool = False


class MetricConfig(BaseModel):
    id: str
    name: str
    type: MetricType
    description: str
    event_name: Optional[str] = None
    success_criteria: Optional[Dict[str, Any]] = None


class ExperimentCreate(BaseModel):
    id: str
    name: str
    description: str
    hypothesis: str
    variants: List[VariantConfig]
    metrics: List[MetricConfig]
    targeting_rules: Optional[Dict[str, Any]] = None
    assignment_method: VariantAssignmentMethod = VariantAssignmentMethod.DETERMINISTIC
    min_sample_size: int = Field(default=1000, ge=100)
    max_duration_days: int = Field(default=30, ge=1, le=90)


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    targeting_rules: Optional[Dict[str, Any]] = None
    max_duration_days: Optional[int] = None


class ExperimentAssignment(BaseModel):
    experiment_id: str
    variant_id: str
    variant_name: str
    config: Dict[str, Any]


class ConversionEvent(BaseModel):
    experiment_id: str
    metric_id: str
    value: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class SampleSizeRequest(BaseModel):
    baseline_rate: float = Field(gt=0, lt=1)
    minimum_detectable_effect: float = Field(gt=0, lt=1)
    power: float = Field(default=0.8, gt=0, lt=1)
    significance_level: float = Field(default=0.05, gt=0, lt=0.5)


# User endpoints (for variant assignment)
@router.get("/assignments")
async def get_user_assignments(
    current_user: User = Depends(get_current_user)
) -> List[ExperimentAssignment]:
    """Get all experiment assignments for current user."""
    assignments = []
    
    for exp_id, experiment in ab_testing_service.experiments.items():
        if experiment.status == ExperimentStatus.RUNNING:
            variant = await ab_testing_service.get_variant(current_user, exp_id)
            if variant:
                assignments.append(ExperimentAssignment(
                    experiment_id=exp_id,
                    variant_id=variant.id,
                    variant_name=variant.name,
                    config=variant.config
                ))
    
    return assignments


@router.get("/assignment/{experiment_id}")
async def get_variant_assignment(
    experiment_id: str,
    current_user: User = Depends(get_current_user)
) -> Optional[ExperimentAssignment]:
    """Get variant assignment for specific experiment."""
    variant = await ab_testing_service.get_variant(current_user, experiment_id)
    
    if not variant:
        return None
    
    return ExperimentAssignment(
        experiment_id=experiment_id,
        variant_id=variant.id,
        variant_name=variant.name,
        config=variant.config
    )


@router.post("/track")
async def track_conversion(
    event: ConversionEvent,
    current_user: User = Depends(get_current_user)
):
    """Track a conversion event."""
    await ab_testing_service.track_conversion(
        user_id=str(current_user.id),
        experiment_id=event.experiment_id,
        metric_id=event.metric_id,
        value=event.value,
        metadata=event.metadata
    )
    
    return {"status": "tracked"}


# Admin endpoints
@router.get("/list", dependencies=[Depends(require_admin)])
async def list_experiments(
    status: Optional[ExperimentStatus] = None,
    include_archived: bool = False
):
    """List all experiments."""
    experiments = []
    
    for experiment in ab_testing_service.experiments.values():
        if status and experiment.status != status:
            continue
        if not include_archived and experiment.status == ExperimentStatus.ARCHIVED:
            continue
        
        experiments.append({
            "id": experiment.id,
            "name": experiment.name,
            "status": experiment.status,
            "created_at": experiment.created_at,
            "started_at": experiment.started_at,
            "ended_at": experiment.ended_at,
            "variants_count": len(experiment.variants),
            "metrics_count": len(experiment.metrics)
        })
    
    return experiments


@router.get("/{experiment_id}", dependencies=[Depends(require_admin)])
async def get_experiment(experiment_id: str):
    """Get experiment details."""
    experiment = ab_testing_service.experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "hypothesis": experiment.hypothesis,
        "status": experiment.status,
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "weight": v.weight,
                "config": v.config,
                "is_control": v.is_control
            }
            for v in experiment.variants
        ],
        "metrics": [
            {
                "id": m.id,
                "name": m.name,
                "type": m.type,
                "description": m.description,
                "event_name": m.event_name,
                "is_primary": m.is_primary()
            }
            for m in experiment.metrics
        ],
        "targeting_rules": experiment.targeting_rules,
        "assignment_method": experiment.assignment_method,
        "min_sample_size": experiment.min_sample_size,
        "max_duration_days": experiment.max_duration_days,
        "created_at": experiment.created_at,
        "started_at": experiment.started_at,
        "ended_at": experiment.ended_at
    }


@router.post("/create", dependencies=[Depends(require_admin)])
async def create_experiment(config: ExperimentCreate):
    """Create a new experiment."""
    try:
        # Convert to internal models
        variants = [
            Variant(
                id=v.id,
                name=v.name,
                description=v.description,
                weight=v.weight,
                config=v.config,
                is_control=v.is_control
            )
            for v in config.variants
        ]
        
        metrics = [
            Metric(
                id=m.id,
                name=m.name,
                type=m.type,
                description=m.description,
                event_name=m.event_name,
                success_criteria=m.success_criteria
            )
            for m in config.metrics
        ]
        
        experiment = Experiment(
            id=config.id,
            name=config.name,
            description=config.description,
            hypothesis=config.hypothesis,
            variants=variants,
            metrics=metrics,
            targeting_rules=config.targeting_rules,
            assignment_method=config.assignment_method,
            min_sample_size=config.min_sample_size,
            max_duration_days=config.max_duration_days
        )
        
        ab_testing_service.create_experiment(experiment)
        
        return {"id": experiment.id, "status": "created"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{experiment_id}", dependencies=[Depends(require_admin)])
async def update_experiment(
    experiment_id: str,
    update: ExperimentUpdate
):
    """Update experiment details (only for draft experiments)."""
    experiment = ab_testing_service.experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if experiment.status != ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only update experiments in DRAFT status"
        )
    
    # Apply updates
    if update.name is not None:
        experiment.name = update.name
    if update.description is not None:
        experiment.description = update.description
    if update.hypothesis is not None:
        experiment.hypothesis = update.hypothesis
    if update.targeting_rules is not None:
        experiment.targeting_rules = update.targeting_rules
    if update.max_duration_days is not None:
        experiment.max_duration_days = update.max_duration_days
    
    return {"status": "updated"}


@router.post("/{experiment_id}/start", dependencies=[Depends(require_admin)])
async def start_experiment(experiment_id: str):
    """Start running an experiment."""
    try:
        ab_testing_service.start_experiment(experiment_id)
        return {"status": "started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/stop", dependencies=[Depends(require_admin)])
async def stop_experiment(
    experiment_id: str,
    reason: str = Query("", description="Reason for stopping")
):
    """Stop a running experiment."""
    try:
        ab_testing_service.stop_experiment(experiment_id, reason)
        return {"status": "stopped"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{experiment_id}/results", dependencies=[Depends(require_admin)])
async def get_experiment_results(
    experiment_id: str,
    metric_id: Optional[str] = None,
    confidence_level: float = Query(default=0.95, ge=0.5, le=0.99)
):
    """Get experiment results and analysis."""
    experiment = ab_testing_service.experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # If no metric specified, use primary metric
    if not metric_id:
        primary_metric = experiment.get_primary_metric()
        if not primary_metric:
            raise HTTPException(status_code=400, detail="No primary metric defined")
        metric_id = primary_metric.id
    
    results = ab_testing_service.analyze_experiment(
        experiment_id,
        metric_id,
        confidence_level
    )
    
    # Check for winner
    winning_variant = ab_testing_service.get_winning_variant(
        experiment_id,
        metric_id
    )
    
    return {
        "experiment_id": experiment_id,
        "metric_id": metric_id,
        "confidence_level": confidence_level,
        "results": [
            {
                "variant_id": r.variant_id,
                "variant_name": next(v.name for v in experiment.variants if v.id == r.variant_id),
                "sample_size": r.sample_size,
                "conversions": r.conversions,
                "conversion_rate": r.conversion_rate,
                "confidence_interval": r.confidence_interval,
                "p_value": r.p_value,
                "is_significant": r.is_significant,
                "lift": r.lift
            }
            for r in results
        ],
        "winning_variant": winning_variant,
        "status": experiment.status
    }


@router.post("/calculate-sample-size", dependencies=[Depends(require_admin)])
async def calculate_sample_size(request: SampleSizeRequest):
    """Calculate required sample size for an experiment."""
    sample_size = ab_testing_service.calculate_sample_size(
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
        power=request.power,
        significance_level=request.significance_level
    )
    
    return {
        "sample_size_per_variant": sample_size,
        "total_sample_size": sample_size * 2,  # For A/B test
        "parameters": {
            "baseline_rate": request.baseline_rate,
            "minimum_detectable_effect": request.minimum_detectable_effect,
            "power": request.power,
            "significance_level": request.significance_level
        }
    }


@router.get("/{experiment_id}/duration", dependencies=[Depends(require_admin)])
async def estimate_duration(
    experiment_id: str,
    daily_traffic: int = Query(gt=0)
):
    """Estimate how long an experiment needs to run."""
    days = ab_testing_service.estimate_experiment_duration(
        experiment_id,
        daily_traffic
    )
    
    if days == 0:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "estimated_days": days,
        "daily_traffic": daily_traffic
    }


# Pre-defined experiment templates
@router.get("/templates/list", dependencies=[Depends(require_admin)])
async def list_experiment_templates():
    """Get available experiment templates."""
    return [
        {
            "id": "pricing_page",
            "name": "Pricing Page Optimization",
            "description": "Test different pricing page layouts"
        },
        {
            "id": "onboarding_flow",
            "name": "Onboarding Flow Test",
            "description": "Optimize user onboarding completion"
        },
        {
            "id": "email_frequency",
            "name": "Email Frequency Test",
            "description": "Find optimal email communication frequency"
        }
    ]


@router.get("/templates/{template_id}", dependencies=[Depends(require_admin)])
async def get_experiment_template(template_id: str):
    """Get a specific experiment template."""
    templates = {
        "pricing_page": ExperimentLibrary.pricing_page_experiment,
        "onboarding_flow": ExperimentLibrary.onboarding_flow_experiment,
        "email_frequency": ExperimentLibrary.email_frequency_experiment
    }
    
    if template_id not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
    
    experiment = templates[template_id]()
    
    return {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "hypothesis": experiment.hypothesis,
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "weight": v.weight,
                "config": v.config,
                "is_control": v.is_control
            }
            for v in experiment.variants
        ],
        "metrics": [
            {
                "id": m.id,
                "name": m.name,
                "type": m.type,
                "description": m.description,
                "event_name": m.event_name,
                "success_criteria": m.success_criteria
            }
            for m in experiment.metrics
        ],
        "targeting_rules": experiment.targeting_rules,
        "assignment_method": experiment.assignment_method,
        "min_sample_size": experiment.min_sample_size,
        "max_duration_days": experiment.max_duration_days
    }