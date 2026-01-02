"""Cost comparison service with side-by-side cost comparisons for different configurations."""

from typing import List, Dict, Any
from ...models.pricing_calculation import PricingCalculation


class CostComparisonService:
    """Provides cost comparisons between different configurations."""

    @staticmethod
    def compare_configurations(
        calculations: List[PricingCalculation],
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compare multiple pricing calculations.

        Args:
            calculations: List of pricing calculations
            labels: Optional labels for each calculation

        Returns:
            Comparison result
        """
        if not labels:
            labels = [f"Configuration {i+1}" for i in range(len(calculations))]

        comparison = {
            "configurations": [],
            "total_costs": [],
            "cost_differences": {},
            "recommendation": None,
        }

        for i, (calc, label) in enumerate(zip(calculations, labels)):
            total = float(calc.total_monthly_cost)
            comparison["configurations"].append({
                "label": label,
                "total_monthly_cost": total,
                "cost_breakdown": [
                    {
                        "service": cost.service_name,
                        "monthly_cost": float(cost.monthly_cost),
                    }
                    for cost in calc.cost_breakdown
                ],
            })
            comparison["total_costs"].append(total)

        # Calculate differences
        if len(comparison["total_costs"]) > 1:
            base_cost = comparison["total_costs"][0]
            for i, cost in enumerate(comparison["total_costs"][1:], 1):
                diff = cost - base_cost
                diff_pct = (diff / base_cost * 100) if base_cost > 0 else 0
                comparison["cost_differences"][f"{labels[0]} vs {labels[i]}"] = {
                    "absolute": diff,
                    "percentage": diff_pct,
                }

        # Find cheapest option
        if comparison["total_costs"]:
            min_index = comparison["total_costs"].index(min(comparison["total_costs"]))
            comparison["recommendation"] = {
                "label": labels[min_index],
                "total_cost": comparison["total_costs"][min_index],
            }

        return comparison

    @staticmethod
    def format_comparison(comparison: Dict[str, Any]) -> str:
        """Format comparison result as text.

        Args:
            comparison: Comparison result

        Returns:
            Formatted comparison text
        """
        lines = ["## 成本对比\n"]

        for config in comparison["configurations"]:
            lines.append(f"### {config['label']}")
            lines.append(f"**总月成本**: ${config['total_monthly_cost']:.2f}")
            lines.append("\n**成本明细:**")
            for item in config["cost_breakdown"]:
                lines.append(f"- {item['service']}: ${item['monthly_cost']:.2f}")
            lines.append("")

        if comparison["cost_differences"]:
            lines.append("### 成本差异")
            for label, diff in comparison["cost_differences"].items():
                lines.append(f"{label}: ${diff['absolute']:.2f} ({diff['percentage']:+.1f}%)")

        if comparison["recommendation"]:
            rec = comparison["recommendation"]
            lines.append(f"\n**推荐**: {rec['label']} (最低成本: ${rec['total_cost']:.2f}/月)")

        return "\n".join(lines)

