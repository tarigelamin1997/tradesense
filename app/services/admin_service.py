
"""
Admin Service
Handles admin dashboard, user management, and system monitoring functionality
"""

import logging
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdminService:
    """Complete admin service implementation"""
    
    def __init__(self):
        self.db_path = 'tradesense.db'
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get admin dashboard overview statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user stats
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # Get recent signups (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (week_ago,))
                recent_signups = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # Get trade stats
                cursor.execute("SELECT COUNT(*) FROM trades")
                total_trades = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                return {
                    "total_users": total_users,
                    "recent_signups": recent_signups,
                    "total_trades": total_trades,
                    "active_sessions": 0,  # Placeholder - would need session tracking
                    "system_health": "OK",
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Dashboard stats failed: {e}")
            # Return safe defaults if database fails
            return {
                "total_users": 0,
                "recent_signups": 0,
                "total_trades": 0,
                "active_sessions": 0,
                "system_health": "ERROR",
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_users(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get paginated user list"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, created_at, is_admin 
                    FROM users 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        "id": row[0],
                        "username": row[1],
                        "email": row[2],
                        "created_at": row[3],
                        "is_admin": bool(row[4])
                    })
                
                return users
        except Exception as e:
            logger.error(f"Get users failed: {e}")
            return []
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Check database connectivity
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_status = "OK"
            
            # Basic system metrics
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                "database": db_status,
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available,
                "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "database": "ERROR",
                "cpu_usage": 0,
                "memory_usage": 0,
                "memory_available": 0,
                "status": "error"
            }
    
    async def disable_user(self, user_id: int) -> bool:
        """Disable user account"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET is_active = 0 WHERE id = ?
                """, (user_id,))
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Disable user failed: {e}")
            return False
    
    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get platform usage analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trade volume by day (last 30 days)
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("""
                    SELECT DATE(entry_time) as trade_date, COUNT(*) as trade_count
                    FROM trades 
                    WHERE entry_time > ?
                    GROUP BY DATE(entry_time)
                    ORDER BY trade_date
                """, (thirty_days_ago,))
                
                daily_trades = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                # Get most active users
                cursor.execute("""
                    SELECT user_id, COUNT(*) as trade_count
                    FROM trades
                    GROUP BY user_id
                    ORDER BY trade_count DESC
                    LIMIT 10
                """)
                
                top_users = [{"user_id": row[0], "trade_count": row[1]} for row in cursor.fetchall()]
                
                return {
                    "daily_trades": daily_trades,
                    "top_users": top_users,
                    "analytics_generated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Usage analytics failed: {e}")
            return {
                "daily_trades": [],
                "top_users": [],
                "analytics_generated": datetime.now().isoformat()
            }
