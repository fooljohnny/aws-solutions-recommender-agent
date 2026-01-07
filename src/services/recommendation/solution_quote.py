"""Generate configuration checklist and pricing estimate for a chosen solution.

This module is designed to be called after the user selects a solution template.
It outputs:
- A table-form configuration checklist (service/SKU/spec/params/AZ/quantity)
- A rough pricing estimate table (if unit prices are available)

Pricing sources:
- Prefer AWS Pricing Calculator service (existing `PricingCalculator`) in runtime
- For deterministic behavior (tests / offline), allow passing explicit unit prices per SKU
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ..product_catalog.models import ProductOffering


@dataclass(frozen=True)
class QuoteTables:
    config_table_markdown: str
    pricing_table_markdown: str
    total_monthly_cost: Optional[Decimal]


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join([head, sep, body]).strip()


def _fmt_money(x: Optional[Decimal]) -> str:
    if x is None:
        return "N/A"
    return f"${x:.2f}"


class SolutionQuoteService:
    """Turn fulfillment plan into tables.

    Inputs:
    - fulfillment: per-service dict created by `SolutionKBRecommendationService`
    - unit_price_per_hour_by_sku: optional pricing lookup to avoid calling AWS APIs
    """

    def build_tables(
        self,
        *,
        fulfillment: Dict[str, Dict[str, object]],
        unit_price_per_hour_by_sku: Optional[Dict[str, float]] = None,
    ) -> QuoteTables:
        unit_price_per_hour_by_sku = unit_price_per_hour_by_sku or {}

        config_rows: List[List[str]] = []
        pricing_rows: List[List[str]] = []

        total: Decimal = Decimal("0.00")
        any_priced = False

        for service_name, info in fulfillment.items():
            sku = str(info.get("sku", ""))
            spec = info.get("spec") or {}
            defaults = info.get("defaults") or {}
            qty = int(info.get("quantity", 1) or 1)
            azs = info.get("chosen_azs") or []

            config_rows.append(
                [
                    service_name,
                    sku or "-",
                    ", ".join([f"{k}={v}" for k, v in spec.items()]) or "-",
                    str(qty),
                    ", ".join([str(a) for a in azs]) or "-",
                    ", ".join([f"{k}={v}" for k, v in defaults.items()]) or "-",
                ]
            )

            unit = unit_price_per_hour_by_sku.get(sku)
            if unit is None:
                pricing_rows.append([service_name, sku or "-", "N/A", str(qty), "N/A"])
                continue

            hourly = Decimal(str(unit))
            monthly = hourly * Decimal("730") * Decimal(str(qty))
            any_priced = True
            total += monthly
            pricing_rows.append([service_name, sku or "-", f"${hourly:.4f}/hr", str(qty), _fmt_money(monthly)])

        config_table = _md_table(
            ["Service", "SKU", "Spec", "Qty", "AZ(s)", "Default params"],
            config_rows or [["-", "-", "-", "-", "-", "-"]],
        )
        pricing_table = _md_table(
            ["Service", "SKU", "Unit price", "Qty", "Est. monthly"],
            pricing_rows or [["-", "-", "-", "-", "-"]],
        )

        return QuoteTables(
            config_table_markdown=config_table,
            pricing_table_markdown=pricing_table,
            total_monthly_cost=total if any_priced else None,
        )

