"""DynamoDB client wrapper with connection and table management."""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel


class DynamoDBClient:
    """DynamoDB client wrapper for connection and table management."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """Initialize DynamoDB client.

        Args:
            region_name: AWS region name (defaults to AWS_REGION env var)
            endpoint_url: Optional endpoint URL for local testing
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = endpoint_url
        self.client = boto3.client(
            "dynamodb",
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
        )
        self.resource = boto3.resource(
            "dynamodb",
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
        )

    def create_conversations_table(
        self,
        table_name: Optional[str] = None,
        read_capacity: int = 5,
        write_capacity: int = 5,
    ) -> str:
        """Create conversations table with TTL support.

        Args:
            table_name: Table name (defaults to DYNAMODB_TABLE_CONVERSATIONS env var)
            read_capacity: Read capacity units
            write_capacity: Write capacity units

        Returns:
            Created table name
        """
        table_name = table_name or os.getenv("DYNAMODB_TABLE_CONVERSATIONS", "conversations")
        try:
            table = self.resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "session_id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "session_id", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",  # Use on-demand billing
            )
            # Wait for table to be created
            table.wait_until_exists()
            return table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                return table_name  # Table already exists
            raise

    def create_messages_table(
        self,
        table_name: Optional[str] = None,
        read_capacity: int = 5,
        write_capacity: int = 5,
    ) -> str:
        """Create messages table with session_id and timestamp as composite key.

        Args:
            table_name: Table name (defaults to DYNAMODB_TABLE_MESSAGES env var)
            read_capacity: Read capacity units
            write_capacity: Write capacity units

        Returns:
            Created table name
        """
        table_name = table_name or os.getenv("DYNAMODB_TABLE_MESSAGES", "messages")
        try:
            table = self.resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "session_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "session_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            return table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                return table_name
            raise

    def create_recommendations_table(
        self,
        table_name: Optional[str] = None,
        read_capacity: int = 5,
        write_capacity: int = 5,
    ) -> str:
        """Create recommendations table with session_id and created_at as composite key.

        Args:
            table_name: Table name (defaults to DYNAMODB_TABLE_RECOMMENDATIONS env var)
            read_capacity: Read capacity units
            write_capacity: Write capacity units

        Returns:
            Created table name
        """
        table_name = table_name or os.getenv("DYNAMODB_TABLE_RECOMMENDATIONS", "recommendations")
        try:
            table = self.resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "session_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "session_id", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            return table_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                return table_name
            raise

    def initialize_tables(self) -> Dict[str, str]:
        """Initialize all required tables.

        Returns:
            Dictionary mapping table type to table name
        """
        return {
            "conversations": self.create_conversations_table(),
            "messages": self.create_messages_table(),
            "recommendations": self.create_recommendations_table(),
        }

    def get_table(self, table_name: str):
        """Get DynamoDB table resource.

        Args:
            table_name: Table name

        Returns:
            DynamoDB table resource
        """
        return self.resource.Table(table_name)

