from decimal import Decimal

from src.services.recommendation.solution_config_modifier import SolutionConfigModifier
from src.services.recommendation.solution_quote import SolutionQuoteService


def test_quote_tables_render_and_sum():
    fulfillment = {
        "EC2": {
            "sku": "ec2.t3.medium.us-east-1",
            "spec": {"instance_type": "t3.medium"},
            "defaults": {"os": "linux"},
            "quantity": 2,
            "chosen_azs": ["us-east-1a"],
        },
        "RDS": {
            "sku": "rds.db.t3.medium.us-east-1",
            "spec": {"instance_class": "db.t3.medium"},
            "defaults": {"engine": "mysql"},
            "quantity": 1,
            "chosen_azs": ["us-east-1a", "us-east-1b"],
        },
    }

    quote = SolutionQuoteService().build_tables(
        fulfillment=fulfillment,
        unit_price_per_hour_by_sku={
            "ec2.t3.medium.us-east-1": 0.0416,
            "rds.db.t3.medium.us-east-1": 0.067,
        },
    )

    assert "EC2" in quote.config_table_markdown
    assert "RDS" in quote.config_table_markdown
    assert quote.total_monthly_cost is not None
    # Deterministic: (0.0416*730*2) + (0.067*730*1)
    expected = (Decimal("0.0416") * Decimal("730") * Decimal("2")) + (Decimal("0.067") * Decimal("730"))
    assert quote.total_monthly_cost == expected


def test_modifier_parses_and_applies_changes():
    fulfillment = {
        "EC2": {
            "sku": "ec2.t3.medium.us-east-1",
            "spec": {"instance_type": "t3.medium"},
            "defaults": {"os": "linux"},
            "quantity": 1,
            "chosen_azs": ["us-east-1a"],
        }
    }

    modder = SolutionConfigModifier()
    mod = modder.parse("把可用区改成 us-east-1c，EC2 两台，实例用 t3.large，multi_az=false")
    newf = modder.apply_to_fulfillment(fulfillment, mod)

    assert newf["EC2"]["quantity"] == 2
    assert newf["EC2"]["spec"]["instance_type"] == "t3.large"
    assert newf["EC2"]["chosen_azs"] == ["us-east-1c"]
    assert newf["EC2"]["defaults"]["multi_az"] is False

