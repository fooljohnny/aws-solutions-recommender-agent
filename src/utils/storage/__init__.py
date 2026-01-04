"""Storage utilities for MySQL, Redis, and Milvus."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

# Try to import MySQL client
try:
    from .mysql import MySQLClient
    _mysql_available = True
except ImportError:
    _mysql_available = False

from .sqlite import SQLiteClient

if TYPE_CHECKING:
    from .mysql import MySQLClient as MySQLClientType


def get_storage_client(storage_client=None) -> Union["MySQLClient", SQLiteClient]:
    """Get storage client based on DATABASE_TYPE environment variable.
    
    Args:
        storage_client: Optional pre-configured storage client. If provided, returns it directly.
    
    Returns:
        MySQLClient or SQLiteClient instance
        
    Environment Variables:
        DATABASE_TYPE: 'mysql' or 'sqlite' (default: 'sqlite')
        SQLITE_DB_PATH: Path to SQLite database file (optional, defaults to ./data/aws_arch_agent.db)
        MYSQL_HOST: MySQL host (default: localhost)
        MYSQL_PORT: MySQL port (default: 3306)
        MYSQL_USER: MySQL user (default: root)
        MYSQL_PASSWORD: MySQL password
        MYSQL_DATABASE: MySQL database name (default: aws_arch_agent)
    """
    if storage_client:
        return storage_client
    
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    if database_type == "mysql":
        if not _mysql_available:
            print("[WARNING] MySQL not available, falling back to SQLite")
            return SQLiteClient()
        try:
            return MySQLClient()
        except Exception as e:
            print(f"[WARNING] Failed to initialize MySQL, falling back to SQLite: {e}")
            return SQLiteClient()
    else:
        # Default to SQLite
        db_path = os.getenv("SQLITE_DB_PATH")
        return SQLiteClient(db_path=db_path)

