"""MySQL client wrapper with connection and database management."""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import aiomysql


class MySQLClient:
    """MySQL client wrapper for connection and database management."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 3306,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """Initialize MySQL client.

        Args:
            host: MySQL host (defaults to MYSQL_HOST env var or localhost)
            port: MySQL port (defaults to MYSQL_PORT env var or 3306)
            user: MySQL user (defaults to MYSQL_USER env var or root)
            password: MySQL password (defaults to MYSQL_PASSWORD env var)
            database: Database name (defaults to MYSQL_DATABASE env var or aws_arch_agent)
        """
        self.host = host or os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", str(port)))
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "")
        self.database = database or os.getenv("MYSQL_DATABASE", "aws_arch_agent")
        self.pool = None

    async def connect(self):
        """Create connection pool."""
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=10,
            )

    async def close(self):
        """Close connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query result
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()

    async def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Single row as dictionary or None
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchone()

    async def execute_many(self, query: str, params_list: list) -> int:
        """Execute a query multiple times.

        Args:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                return await cursor.executemany(query, params_list)

    async def initialize_database(self):
        """Initialize database and create tables if they don't exist."""
        # First, create database if it doesn't exist
        temp_pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            charset="utf8mb4",
            autocommit=True,
        )

        async with temp_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        temp_pool.close()
        await temp_pool.wait_closed()

        # Now connect to the database
        await self.connect()

        # Create tables
        await self._create_conversations_table()
        await self._create_messages_table()
        await self._create_intents_table()
        await self._create_user_requirements_table()
        await self._create_recommendations_table()

    async def _create_conversations_table(self):
        """Create conversations table."""
        query = """
        CREATE TABLE IF NOT EXISTS conversations (
            session_id VARCHAR(36) PRIMARY KEY,
            created_at DATETIME NOT NULL,
            last_accessed_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL,
            conversation_history JSON,
            current_context JSON,
            user_preferences JSON,
            INDEX idx_expires_at (expires_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        await self.execute(query)

    async def _create_messages_table(self):
        """Create messages table."""
        query = """
        CREATE TABLE IF NOT EXISTS messages (
            message_id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            timestamp DATETIME NOT NULL,
            role ENUM('user', 'assistant') NOT NULL,
            content TEXT NOT NULL,
            intents JSON,
            metadata JSON,
            INDEX idx_session_timestamp (session_id, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        await self.execute(query)

    async def _create_intents_table(self):
        """Create intents table."""
        query = """
        CREATE TABLE IF NOT EXISTS intents (
            intent_id VARCHAR(36) PRIMARY KEY,
            message_id VARCHAR(36) NOT NULL,
            intent_type VARCHAR(50) NOT NULL,
            priority INT NOT NULL,
            confidence FLOAT NOT NULL,
            extracted_entities JSON,
            status VARCHAR(20) NOT NULL,
            INDEX idx_message_id (message_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        await self.execute(query)

    async def _create_user_requirements_table(self):
        """Create user_requirements table."""
        query = """
        CREATE TABLE IF NOT EXISTS user_requirements (
            requirement_id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            extracted_at DATETIME NOT NULL,
            requirement_type VARCHAR(50) NOT NULL,
            requirement_value TEXT NOT NULL,
            confidence FLOAT NOT NULL,
            source_message_id VARCHAR(36),
            INDEX idx_session_id (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        await self.execute(query)

    async def _create_recommendations_table(self):
        """Create recommendations table."""
        query = """
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            created_at DATETIME NOT NULL,
            services JSON,
            configurations JSON,
            diagram_data TEXT,
            diagram_url VARCHAR(500),
            pricing JSON,
            well_architected_alignment JSON,
            explanation TEXT,
            INDEX idx_session_id (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        await self.execute(query)

