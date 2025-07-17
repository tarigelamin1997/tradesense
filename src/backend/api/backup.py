"""
Backup management API endpoints for TradeSense.
Handles backup operations, scheduling, and restoration.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from core.auth import get_current_user
from models.user import User
from src.backend.api.admin import require_admin
from src.backend.backup.backup_service import backup_service, BackupType

router = APIRouter(prefix="/api/v1/backup", tags=["backup"])


# Request/Response models
class BackupRequest(BaseModel):
    backup_type: str = "full"  # database, files, full
    destination: Optional[str] = "local"  # local, s3
    compress: bool = True
    encrypt: bool = False


class RestoreRequest(BaseModel):
    backup_id: str
    target_database: Optional[str] = None
    verify_first: bool = True


class BackupScheduleCreate(BaseModel):
    name: str
    backup_type: str
    schedule_type: str  # cron, interval, time
    schedule_config: dict
    destination: str = "local"
    is_active: bool = True


class BackupScheduleUpdate(BaseModel):
    name: Optional[str] = None
    schedule_config: Optional[dict] = None
    destination: Optional[str] = None
    is_active: Optional[bool] = None


class BackupInfo(BaseModel):
    id: str
    backup_name: str
    backup_type: str
    status: str
    file_size: Optional[int] = None
    remote_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Admin endpoints
@router.post("/create", dependencies=[Depends(require_admin)])
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new backup."""
    try:
        if request.backup_type == "database":
            # Run in background for large databases
            background_tasks.add_task(
                backup_service.backup_database,
                backup_type=BackupType.FULL
            )
            return {
                "status": "initiated",
                "message": "Database backup started in background"
            }
            
        elif request.backup_type == "files":
            background_tasks.add_task(backup_service.backup_files)
            return {
                "status": "initiated",
                "message": "Files backup started in background"
            }
            
        elif request.backup_type == "full":
            background_tasks.add_task(backup_service.backup_full)
            return {
                "status": "initiated",
                "message": "Full system backup started in background"
            }
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid backup type. Must be: database, files, or full"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", dependencies=[Depends(require_admin)])
async def list_backups(
    backup_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[BackupInfo]:
    """List all backups with optional filters."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        query = """
            SELECT id, backup_name, backup_type, status, file_size,
                   remote_path, created_at, completed_at, error_message
            FROM backups
            WHERE 1=1
        """
        params = {}
        
        if backup_type:
            query += " AND backup_type = :backup_type"
            params["backup_type"] = backup_type
            
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        async with get_db() as db:
            result = await db.execute(text(query), params)
            backups = result.fetchall()
            
        return [
            BackupInfo(
                id=str(backup.id),
                backup_name=backup.backup_name,
                backup_type=backup.backup_type,
                status=backup.status,
                file_size=backup.file_size,
                remote_path=backup.remote_path,
                created_at=backup.created_at,
                completed_at=backup.completed_at,
                error_message=backup.error_message
            )
            for backup in backups
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backup_id}", dependencies=[Depends(require_admin)])
async def get_backup_details(backup_id: str):
    """Get detailed information about a specific backup."""
    try:
        backup_info = await backup_service._get_backup_info(backup_id)
        if not backup_info:
            raise HTTPException(status_code=404, detail="Backup not found")
            
        return backup_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore", dependencies=[Depends(require_admin)])
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Restore from a backup."""
    try:
        # Verify backup first if requested
        if request.verify_first:
            verification = await backup_service.verify_backup(request.backup_id)
            if verification['status'] != 'passed':
                raise HTTPException(
                    status_code=400,
                    detail=f"Backup verification failed: {verification['checks']}"
                )
        
        # Start restore in background
        background_tasks.add_task(
            backup_service.restore_database,
            backup_id=request.backup_id,
            target_db=request.target_database
        )
        
        return {
            "status": "initiated",
            "message": "Restore operation started in background",
            "backup_id": request.backup_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{backup_id}/verify", dependencies=[Depends(require_admin)])
async def verify_backup(backup_id: str):
    """Verify backup integrity."""
    try:
        result = await backup_service.verify_backup(backup_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup", dependencies=[Depends(require_admin)])
async def cleanup_old_backups():
    """Clean up old backups based on retention policy."""
    try:
        result = await backup_service.cleanup_old_backups()
        return {
            "status": "completed",
            "deleted": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Schedule management
@router.get("/schedules/list", dependencies=[Depends(require_admin)])
async def list_backup_schedules():
    """List all backup schedules."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        async with get_db() as db:
            result = await db.execute(
                text("""
                    SELECT id, name, backup_type, schedule_type,
                           schedule_config, destination, is_active,
                           last_run_at, next_run_at
                    FROM backup_schedules
                    ORDER BY name
                """)
            )
            schedules = result.fetchall()
            
        return [
            {
                "id": str(schedule.id),
                "name": schedule.name,
                "backup_type": schedule.backup_type,
                "schedule_type": schedule.schedule_type,
                "schedule_config": schedule.schedule_config,
                "destination": schedule.destination,
                "is_active": schedule.is_active,
                "last_run_at": schedule.last_run_at,
                "next_run_at": schedule.next_run_at
            }
            for schedule in schedules
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/create", dependencies=[Depends(require_admin)])
async def create_backup_schedule(schedule: BackupScheduleCreate):
    """Create a new backup schedule."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        async with get_db() as db:
            result = await db.execute(
                text("""
                    INSERT INTO backup_schedules (
                        name, backup_type, schedule_type,
                        schedule_config, destination, is_active
                    ) VALUES (
                        :name, :backup_type, :schedule_type,
                        :schedule_config, :destination, :is_active
                    )
                    RETURNING id
                """),
                {
                    "name": schedule.name,
                    "backup_type": schedule.backup_type,
                    "schedule_type": schedule.schedule_type,
                    "schedule_config": schedule.schedule_config,
                    "destination": schedule.destination,
                    "is_active": schedule.is_active
                }
            )
            await db.commit()
            schedule_id = result.scalar()
            
        return {
            "id": str(schedule_id),
            "status": "created",
            "message": f"Backup schedule '{schedule.name}' created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/schedules/{schedule_id}", dependencies=[Depends(require_admin)])
async def update_backup_schedule(
    schedule_id: str,
    update: BackupScheduleUpdate
):
    """Update a backup schedule."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        # Build update query
        updates = []
        params = {"schedule_id": schedule_id}
        
        if update.name is not None:
            updates.append("name = :name")
            params["name"] = update.name
            
        if update.schedule_config is not None:
            updates.append("schedule_config = :schedule_config")
            params["schedule_config"] = update.schedule_config
            
        if update.destination is not None:
            updates.append("destination = :destination")
            params["destination"] = update.destination
            
        if update.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = update.is_active
            
        if not updates:
            return {"message": "No updates provided"}
            
        query = f"""
            UPDATE backup_schedules
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = :schedule_id
        """
        
        async with get_db() as db:
            result = await db.execute(text(query), params)
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Schedule not found")
                
        return {
            "status": "updated",
            "message": "Backup schedule updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedules/{schedule_id}", dependencies=[Depends(require_admin)])
async def delete_backup_schedule(schedule_id: str):
    """Delete a backup schedule."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        async with get_db() as db:
            result = await db.execute(
                text("DELETE FROM backup_schedules WHERE id = :schedule_id"),
                {"schedule_id": schedule_id}
            )
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Schedule not found")
                
        return {
            "status": "deleted",
            "message": "Backup schedule deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Statistics and monitoring
@router.get("/stats/overview", dependencies=[Depends(require_admin)])
async def get_backup_statistics(days: int = 30):
    """Get backup statistics for the specified period."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        async with get_db() as db:
            result = await db.execute(
                text("SELECT * FROM get_backup_statistics(:days)"),
                {"days": days}
            )
            stats = result.fetchall()
            
        return [
            {
                "backup_type": stat.backup_type,
                "total_count": stat.total_count,
                "success_count": stat.success_count,
                "failed_count": stat.failed_count,
                "total_size_gb": float(stat.total_size_gb or 0),
                "avg_duration_minutes": float(stat.avg_duration_minutes or 0),
                "success_rate": float(stat.success_rate or 0)
            }
            for stat in stats
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/dashboard", dependencies=[Depends(require_admin)])
async def get_backup_dashboard():
    """Get backup status dashboard data."""
    try:
        from sqlalchemy import text
        from core.db.session import get_db
        
        async with get_db() as db:
            # Recent backups
            recent_result = await db.execute(
                text("""
                    SELECT * FROM backup_status_dashboard
                    ORDER BY backup_type, status
                """)
            )
            recent_backups = recent_result.fetchall()
            
            # Upcoming backups
            upcoming_result = await db.execute(
                text("SELECT * FROM upcoming_backups LIMIT 10")
            )
            upcoming_backups = upcoming_result.fetchall()
            
        return {
            "recent_backups": [
                {
                    "backup_type": backup.backup_type,
                    "status": backup.status,
                    "count": backup.count,
                    "last_backup": backup.last_backup,
                    "total_size": backup.total_size,
                    "avg_duration_seconds": backup.avg_duration_seconds
                }
                for backup in recent_backups
            ],
            "upcoming_backups": [
                {
                    "name": backup.name,
                    "backup_type": backup.backup_type,
                    "next_run_at": backup.next_run_at,
                    "destination": backup.destination,
                    "hours_until_next": float(backup.hours_until_next or 0)
                }
                for backup in upcoming_backups
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))