"""
Advanced health checks for TradeSense.
Provides detailed health status for all components.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiohttp
import psutil
from sqlalchemy import text

from core.db.session import get_db, engine
from core.cache import redis_client
from core.config import settings


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status of a component."""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.response_time_ms = response_time_ms
        self.checked_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "response_time_ms": self.response_time_ms,
            "checked_at": self.checked_at.isoformat()
        }


class HealthChecker:
    """Performs comprehensive health checks."""
    
    def __init__(self):
        self.checks = {
            "database": self.check_database,
            "redis": self.check_redis,
            "disk_space": self.check_disk_space,
            "memory": self.check_memory,
            "external_apis": self.check_external_apis,
            "background_tasks": self.check_background_tasks,
            "ssl_certificates": self.check_ssl_certificates,
        }
    
    async def check_health(self, detailed: bool = False) -> Dict[str, Any]:
        """Perform health checks on all components."""
        start_time = datetime.utcnow()
        
        # Run all checks concurrently
        check_tasks = []
        for name, check_func in self.checks.items():
            check_tasks.append(check_func())
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        components = {}
        overall_status = HealthStatus.HEALTHY
        
        for i, (name, _) in enumerate(self.checks.items()):
            if isinstance(results[i], Exception):
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(results[i])}"
                )
                overall_status = HealthStatus.UNHEALTHY
            else:
                components[name] = results[i]
                if results[i].status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif results[i].status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Calculate total time
        total_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build response
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "total_time_ms": total_time_ms,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
        
        if detailed:
            response["components"] = {
                name: component.to_dict()
                for name, component in components.items()
            }
        
        return response
    
    async def check_database(self) -> ComponentHealth:
        """Check database health."""
        start_time = datetime.utcnow()
        
        try:
            async with get_db() as db:
                # Check basic connectivity
                result = await db.execute(text("SELECT 1"))
                
                # Check connection pool
                pool_status = engine.pool.status()
                
                # Check database size
                size_result = await db.execute(
                    text("SELECT pg_database_size(current_database()) as size")
                )
                db_size = size_result.scalar()
                
                # Check active connections
                conn_result = await db.execute(
                    text("""
                        SELECT count(*) as active_connections
                        FROM pg_stat_activity
                        WHERE state = 'active'
                    """)
                )
                active_connections = conn_result.scalar()
                
                # Check replication lag (if applicable)
                replication_lag = None
                try:
                    lag_result = await db.execute(
                        text("""
                            SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                            AS replication_lag_seconds
                        """)
                    )
                    replication_lag = lag_result.scalar()
                except:
                    pass
                
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Determine status
            status = HealthStatus.HEALTHY
            message = "Database is healthy"
            
            if response_time > 1000:  # 1 second
                status = HealthStatus.DEGRADED
                message = "Database response time is high"
            elif active_connections > 80:
                status = HealthStatus.DEGRADED
                message = "High number of active connections"
            elif replication_lag and replication_lag > 10:
                status = HealthStatus.DEGRADED
                message = f"Replication lag is {replication_lag:.1f} seconds"
            
            return ComponentHealth(
                name="database",
                status=status,
                message=message,
                details={
                    "pool_status": pool_status,
                    "database_size_mb": db_size / (1024 * 1024),
                    "active_connections": active_connections,
                    "replication_lag_seconds": replication_lag
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )
    
    async def check_redis(self) -> ComponentHealth:
        """Check Redis health."""
        start_time = datetime.utcnow()
        
        try:
            # Ping Redis
            await redis_client.ping()
            
            # Get Redis info
            info = await redis_client.info()
            
            # Check memory usage
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0) or float('inf')
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory != float('inf') else 0
            
            # Check connected clients
            connected_clients = info.get("connected_clients", 0)
            
            # Check evicted keys
            evicted_keys = info.get("evicted_keys", 0)
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Determine status
            status = HealthStatus.HEALTHY
            message = "Redis is healthy"
            
            if response_time > 100:  # 100ms
                status = HealthStatus.DEGRADED
                message = "Redis response time is high"
            elif memory_usage_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"Redis memory usage is {memory_usage_percent:.1f}%"
            elif evicted_keys > 1000:
                status = HealthStatus.DEGRADED
                message = f"Redis has evicted {evicted_keys} keys"
            
            return ComponentHealth(
                name="redis",
                status=status,
                message=message,
                details={
                    "used_memory_mb": used_memory / (1024 * 1024),
                    "memory_usage_percent": memory_usage_percent,
                    "connected_clients": connected_clients,
                    "evicted_keys": evicted_keys,
                    "uptime_days": info.get("uptime_in_days", 0)
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}"
            )
    
    async def check_disk_space(self) -> ComponentHealth:
        """Check disk space health."""
        try:
            partitions = psutil.disk_partitions()
            
            critical_partitions = []
            warning_partitions = []
            
            details = {}
            
            for partition in partitions:
                if partition.mountpoint in ['/', '/var', '/tmp', '/data']:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    details[partition.mountpoint] = {
                        "total_gb": usage.total / (1024 ** 3),
                        "used_gb": usage.used / (1024 ** 3),
                        "free_gb": usage.free / (1024 ** 3),
                        "percent": usage.percent
                    }
                    
                    if usage.percent > 90:
                        critical_partitions.append(partition.mountpoint)
                    elif usage.percent > 80:
                        warning_partitions.append(partition.mountpoint)
            
            # Determine status
            if critical_partitions:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk space on: {', '.join(critical_partitions)}"
            elif warning_partitions:
                status = HealthStatus.DEGRADED
                message = f"Low disk space on: {', '.join(warning_partitions)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk space is healthy"
            
            return ComponentHealth(
                name="disk_space",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk space: {str(e)}"
            )
    
    async def check_memory(self) -> ComponentHealth:
        """Check memory health."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Get process memory
            process = psutil.Process()
            process_memory = process.memory_info()
            
            details = {
                "system": {
                    "total_gb": memory.total / (1024 ** 3),
                    "available_gb": memory.available / (1024 ** 3),
                    "used_percent": memory.percent,
                    "swap_used_percent": swap.percent
                },
                "process": {
                    "rss_mb": process_memory.rss / (1024 ** 2),
                    "vms_mb": process_memory.vms / (1024 ** 2),
                    "percent": process.memory_percent()
                }
            }
            
            # Determine status
            status = HealthStatus.HEALTHY
            message = "Memory usage is healthy"
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"System memory usage is {memory.percent}%"
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                message = f"System memory usage is {memory.percent}%"
            elif swap.percent > 50:
                status = HealthStatus.DEGRADED
                message = f"Swap usage is {swap.percent}%"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory: {str(e)}"
            )
    
    async def check_external_apis(self) -> ComponentHealth:
        """Check external API connectivity."""
        apis_to_check = [
            {
                "name": "Stripe",
                "url": "https://api.stripe.com/v1/health",
                "headers": {"Authorization": f"Bearer {settings.STRIPE_API_KEY}"}
            },
            {
                "name": "SendGrid",
                "url": "https://api.sendgrid.com/v3/health",
                "headers": {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"}
            }
        ]
        
        results = {}
        unhealthy_apis = []
        slow_apis = []
        
        async with aiohttp.ClientSession() as session:
            for api in apis_to_check:
                start_time = datetime.utcnow()
                
                try:
                    async with session.get(
                        api["url"],
                        headers=api.get("headers", {}),
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        
                        results[api["name"]] = {
                            "status_code": response.status,
                            "response_time_ms": response_time,
                            "healthy": response.status < 400
                        }
                        
                        if response.status >= 400:
                            unhealthy_apis.append(api["name"])
                        elif response_time > 1000:
                            slow_apis.append(api["name"])
                            
                except Exception as e:
                    results[api["name"]] = {
                        "error": str(e),
                        "healthy": False
                    }
                    unhealthy_apis.append(api["name"])
        
        # Determine status
        if unhealthy_apis:
            status = HealthStatus.DEGRADED
            message = f"APIs unhealthy: {', '.join(unhealthy_apis)}"
        elif slow_apis:
            status = HealthStatus.DEGRADED
            message = f"APIs slow: {', '.join(slow_apis)}"
        else:
            status = HealthStatus.HEALTHY
            message = "All external APIs are healthy"
        
        return ComponentHealth(
            name="external_apis",
            status=status,
            message=message,
            details=results
        )
    
    async def check_background_tasks(self) -> ComponentHealth:
        """Check background task health."""
        try:
            # Check if task queues are processing
            queue_sizes = {}
            
            # Check various task queues
            for queue_name in ["email", "analytics", "exports", "webhooks"]:
                size = await redis_client.llen(f"queue:{queue_name}")
                queue_sizes[queue_name] = size
            
            # Check for stuck tasks
            stuck_tasks = await redis_client.zcount(
                "tasks:processing",
                0,
                int((datetime.utcnow() - timedelta(minutes=30)).timestamp())
            )
            
            # Check failed tasks
            failed_tasks = await redis_client.llen("tasks:failed")
            
            details = {
                "queue_sizes": queue_sizes,
                "stuck_tasks": stuck_tasks,
                "failed_tasks": failed_tasks
            }
            
            # Determine status
            status = HealthStatus.HEALTHY
            message = "Background tasks are healthy"
            
            total_queued = sum(queue_sizes.values())
            
            if stuck_tasks > 10:
                status = HealthStatus.UNHEALTHY
                message = f"{stuck_tasks} tasks are stuck"
            elif failed_tasks > 100:
                status = HealthStatus.DEGRADED
                message = f"{failed_tasks} failed tasks"
            elif total_queued > 1000:
                status = HealthStatus.DEGRADED
                message = f"{total_queued} tasks queued"
            
            return ComponentHealth(
                name="background_tasks",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return ComponentHealth(
                name="background_tasks",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check background tasks: {str(e)}"
            )
    
    async def check_ssl_certificates(self) -> ComponentHealth:
        """Check SSL certificate health."""
        try:
            import ssl
            import socket
            from datetime import datetime
            
            domains_to_check = [
                "tradesense.com",
                "api.tradesense.com"
            ]
            
            results = {}
            expiring_soon = []
            expired = []
            
            for domain in domains_to_check:
                try:
                    context = ssl.create_default_context()
                    with socket.create_connection((domain, 443), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            cert = ssock.getpeercert()
                            
                            # Parse expiry date
                            not_after = datetime.strptime(
                                cert['notAfter'],
                                '%b %d %H:%M:%S %Y %Z'
                            )
                            
                            days_remaining = (not_after - datetime.utcnow()).days
                            
                            results[domain] = {
                                "expires": not_after.isoformat(),
                                "days_remaining": days_remaining,
                                "issuer": dict(x[0] for x in cert['issuer'])['organizationName']
                            }
                            
                            if days_remaining < 0:
                                expired.append(domain)
                            elif days_remaining < 30:
                                expiring_soon.append(domain)
                                
                except Exception as e:
                    results[domain] = {
                        "error": str(e)
                    }
                    expired.append(domain)
            
            # Determine status
            if expired:
                status = HealthStatus.UNHEALTHY
                message = f"Certificates expired: {', '.join(expired)}"
            elif expiring_soon:
                status = HealthStatus.DEGRADED
                message = f"Certificates expiring soon: {', '.join(expiring_soon)}"
            else:
                status = HealthStatus.HEALTHY
                message = "All SSL certificates are healthy"
            
            return ComponentHealth(
                name="ssl_certificates",
                status=status,
                message=message,
                details=results
            )
            
        except Exception as e:
            return ComponentHealth(
                name="ssl_certificates",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check SSL certificates: {str(e)}"
            )


# Initialize health checker
health_checker = HealthChecker()