"""
Async Task Manager

Provides background task processing and async utilities for performance optimization.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    task_id: str
    function_name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0

class AsyncTaskManager:
    """Manages background tasks and async operations"""
    
    def __init__(self, max_workers: int = 10):
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_results: Dict[str, Any] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers // 2)
        self.lock = threading.Lock()
        self.running = True
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_old_tasks())
    
    def generate_task_id(self, function_name: str) -> str:
        """Generate unique task ID"""
        import uuid
        return f"{function_name}_{uuid.uuid4().hex[:8]}"
    
    def create_task(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a new background task"""
        if not task_id:
            task_id = self.generate_task_id(func.__name__)
        
        with self.lock:
            task_info = TaskInfo(
                task_id=task_id,
                function_name=func.__name__,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow()
            )
            self.tasks[task_id] = task_info
        
        # Schedule task execution
        asyncio.create_task(self._execute_task(task_id, func, *args, **kwargs))
        
        logger.info(f"Created task {task_id} for {func.__name__}")
        return task_id
    
    async def _execute_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> None:
        """Execute a background task"""
        task_info = self.tasks.get(task_id)
        if not task_info:
            return
        
        try:
            # Update status to running
            with self.lock:
                task_info.status = TaskStatus.RUNNING
                task_info.started_at = datetime.utcnow()
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run in thread pool for blocking functions
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool, func, *args, **kwargs
                )
            
            # Update task info
            with self.lock:
                task_info.status = TaskStatus.COMPLETED
                task_info.completed_at = datetime.utcnow()
                task_info.result = result
                task_info.progress = 100.0
            
            # Store result
            self.task_results[task_id] = result
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            # Update task info with error
            with self.lock:
                task_info.status = TaskStatus.FAILED
                task_info.completed_at = datetime.utcnow()
                task_info.error = str(e)
            
            logger.error(f"Task {task_id} failed: {str(e)}")
            logger.error(traceback.format_exc())
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """Get task status and information"""
        return self.tasks.get(task_id)
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result if completed"""
        return self.task_results.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        with self.lock:
            task_info = self.tasks.get(task_id)
            if task_info and task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = datetime.utcnow()
                return True
        return False
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """List tasks with optional filtering"""
        with self.lock:
            tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def _cleanup_old_tasks(self):
        """Clean up old completed/failed tasks"""
        while self.running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                with self.lock:
                    # Remove old completed/failed tasks
                    tasks_to_remove = []
                    for task_id, task_info in self.tasks.items():
                        if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                            task_info.created_at < cutoff_time):
                            tasks_to_remove.append(task_id)
                    
                    for task_id in tasks_to_remove:
                        self.tasks.pop(task_id, None)
                        self.task_results.pop(task_id, None)
                
                if tasks_to_remove:
                    logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in task cleanup: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def shutdown(self):
        """Shutdown the task manager"""
        self.running = False
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

# Global task manager instance
task_manager = AsyncTaskManager()

def background_task(task_id: Optional[str] = None):
    """
    Decorator to run a function as a background task
    
    Args:
        task_id: Optional custom task ID
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return task_manager.create_task(func, *args, task_id=task_id, **kwargs)
        return wrapper
    return decorator

def async_task(func: Callable) -> Callable:
    """
    Decorator to mark a function as async and handle it properly
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Async task {func.__name__} failed: {str(e)}")
            raise
    return wrapper

def run_in_thread_pool(func: Callable) -> Callable:
    """
    Decorator to run a blocking function in thread pool
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(task_manager.thread_pool, func, *args, **kwargs)
    return wrapper

def run_in_process_pool(func: Callable) -> Callable:
    """
    Decorator to run a CPU-intensive function in process pool
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(task_manager.process_pool, func, *args, **kwargs)
    return wrapper

# Example usage functions
@background_task()
def process_trade_data(trade_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process trade data in background"""
    # Simulate processing
    import time
    time.sleep(2)
    
    return {
        "processed_trades": len(trade_data),
        "total_pnl": sum(trade.get("pnl", 0) for trade in trade_data),
        "win_rate": len([t for t in trade_data if t.get("pnl", 0) > 0]) / len(trade_data) if trade_data else 0
    }

@async_task
async def generate_analytics_report(user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate analytics report asynchronously"""
    # Simulate async processing
    await asyncio.sleep(1)
    
    return {
        "user_id": user_id,
        "period": f"{start_date.date()} to {end_date.date()}",
        "total_trades": 150,
        "win_rate": 0.65,
        "profit_factor": 1.85
    }

@run_in_thread_pool
def heavy_calculation(data: List[float]) -> float:
    """CPU-intensive calculation in thread pool"""
    import math
    result = 0.0
    for value in data:
        result += math.sqrt(value) * math.log(value + 1)
    return result 