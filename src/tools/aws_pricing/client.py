"""AWS Pricing API client with boto3 integration for GetProducts and GetPrice."""

import os
import boto3
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
from datetime import datetime


class AWSPricingClient:
    """Client for AWS Pricing API."""

    def __init__(
        self,
        region_name: Optional[str] = None,
    ):
        """Initialize AWS Pricing API client.

        Args:
            region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        # Pricing API is only available in us-east-1 and ap-south-1
        pricing_region = "us-east-1"
        self.client = boto3.client("pricing", region_name=pricing_region)

    def get_product(
        self,
        service_code: str,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Get product pricing information.

        Args:
            service_code: AWS service code (e.g., 'AmazonEC2', 'AmazonRDS')
            filters: Optional filters for product search

        Returns:
            List of product pricing information
        """
        try:
            paginator = self.client.get_paginator("get_products")
            page_iterator = paginator.paginate(
                ServiceCode=service_code,
                Filters=filters or [],
                MaxResults=100,
            )

            products = []
            for page in page_iterator:
                products.extend(page.get("PriceList", []))

            return products
        except ClientError as e:
            raise RuntimeError(f"Failed to get product pricing: {e}")

    def get_price(
        self,
        service_code: str,
        instance_type: Optional[str] = None,
        region: Optional[str] = None,
        operating_system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get price for specific service configuration.

        Args:
            service_code: AWS service code
            instance_type: Instance type (for EC2/RDS)
            region: AWS region
            operating_system: Operating system (for EC2)

        Returns:
            Price information
        """
        filters = []

        if service_code == "AmazonEC2":
            if instance_type:
                filters.append({
                    "Type": "TERM_MATCH",
                    "Field": "instanceType",
                    "Value": instance_type,
                })
            if operating_system:
                filters.append({
                    "Type": "TERM_MATCH",
                    "Field": "operatingSystem",
                    "Value": operating_system,
                })
            if region:
                filters.append({
                    "Type": "TERM_MATCH",
                    "Field": "location",
                    "Value": self._get_location_name(region),
                })

        products = self.get_product(service_code, filters)

        if not products:
            return {"price": None, "currency": "USD"}

        # Parse first product's pricing
        import json
        product = json.loads(products[0])
        terms = product.get("terms", {})
        on_demand = terms.get("OnDemand", {})

        price = None
        for term_key, term_value in on_demand.items():
            price_dimensions = term_value.get("priceDimensions", {})
            for dim_key, dim_value in price_dimensions.items():
                price_info = dim_value.get("pricePerUnit", {})
                if "USD" in price_info:
                    price = float(price_info["USD"])
                    break
            if price:
                break

        return {
            "price": price,
            "currency": "USD",
            "unit": "per hour",
            "service_code": service_code,
            "instance_type": instance_type,
        }

    def _get_location_name(self, region: str) -> str:
        """Convert AWS region code to location name for Pricing API.

        Args:
            region: AWS region code

        Returns:
            Location name for Pricing API
        """
        location_map = {
            "us-east-1": "US East (N. Virginia)",
            "us-west-2": "US West (Oregon)",
            "eu-west-1": "Europe (Ireland)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "cn-north-1": "China (Beijing)",
        }
        return location_map.get(region, region)

