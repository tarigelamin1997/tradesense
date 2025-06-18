
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator

class DatabaseManager:
    """Thread-safe database manager with connection pooling."""
    
    def __init__(self, db_path: str = "tradesense.db", max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._local = threading.local()
        self._connection_count = 0
        self._lock = threading.Lock()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            with self._lock:
                if self._connection_count >= self.max_connections:
                    raise Exception("Maximum database connections reached")
                
                self._local.connection = sqlite3.connect(
                    self.db_path, 
                    check_same_thread=False,
                    timeout=30.0
                )
                self._local.connection.row_factory = sqlite3.Row
                self._connection_count += 1
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database operations."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def close_connection(self):
        """Close thread-local connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
            with self._lock:
                self._connection_count -= 1

# Global database manager instance
db_manager = DatabaseManager()
