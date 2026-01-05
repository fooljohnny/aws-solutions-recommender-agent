"""SQLite client wrapper as fallback when MySQL is not available."""

import os
import json
import sqlite3
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path


class SQLiteClient:
    """SQLite client wrapper for connection and database management."""

    def __init__(
        self,
        db_path: Optional[str] = None,
    ):
        """Initialize SQLite client.

        Args:
            db_path: Path to SQLite database file (defaults to SQLITE_DB_PATH env var or ./data/aws_arch_agent.db)
        """
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH")
        
        if db_path is None:
            data_dir = Path("./data")
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "aws_arch_agent.db")
        
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Create connection."""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            await self.initialize_database()

    async def close(self):
        """Close connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def execute(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query.

        Args:
            query: SQL query (with ? placeholders for SQLite)
            params: Query parameters

        Returns:
            Query result as list of dicts
        """
        if self.conn is None:
            await self.connect()

        # Convert MySQL syntax to SQLite if needed
        # But preserve INSERT OR REPLACE and other SQLite-specific syntax
        if "%s" in query and "INSERT OR REPLACE" not in query.upper():
            query = query.replace("%s", "?")
        
        cursor = await self.conn.execute(query, params or ())
        await self.conn.commit()
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Single row as dict or None
        """
        rows = await self.execute(query, params)
        return rows[0] if rows else None

    async def initialize_database(self):
        """Initialize database and create tables if they don't exist."""
        await self._create_conversations_table()
        await self._create_messages_table()
        await self._create_intents_table()
        await self._create_user_requirements_table()
        await self._create_recommendations_table()

    async def _create_conversations_table(self):
        """Create conversations table."""
        query = """
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            last_accessed_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            conversation_history TEXT,
            current_context TEXT,
            user_preferences TEXT
        )
        """
        await self.execute(query)
        
        # Create index
        await self.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON conversations(expires_at)")

    async def _create_messages_table(self):
        """Create messages table."""
        query = """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intents TEXT,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
        )
        """
        await self.execute(query)
        
        # Create index
        await self.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)")

    async def _create_intents_table(self):
        """Create intents table."""
        query = """
        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            intent_type TEXT NOT NULL,
            priority INTEGER NOT NULL,
            confidence REAL NOT NULL,
            extracted_entities TEXT,
            status TEXT NOT NULL
        )
        """
        await self.execute(query)
        
        # Create index
        await self.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON intents(message_id)")

    async def _create_user_requirements_table(self):
        """Create user_requirements table."""
        query = """
        CREATE TABLE IF NOT EXISTS user_requirements (
            requirement_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            extracted_at TEXT NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement_value TEXT NOT NULL,
            confidence REAL,
            source_message_id TEXT,
            FOREIGN KEY (session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
        )
        """
        await self.execute(query)

    async def _create_recommendations_table(self):
        """Create architecture_recommendations table."""
        query = """
        CREATE TABLE IF NOT EXISTS architecture_recommendations (
            recommendation_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            services TEXT,
            configurations TEXT,
            diagram_data TEXT,
            diagram_url TEXT,
            pricing TEXT,
            well_architected_alignment TEXT,
            explanation TEXT,
            FOREIGN KEY (session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
        )
        """
        await self.execute(query)

