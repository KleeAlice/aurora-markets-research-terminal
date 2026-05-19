from __future__ import annotations

from new_energy_broker.schemas import DcfAssumptions
from new_energy_broker.services import (
    build_report,
    calculate_dcf,
    calculate_metrics,
    get_peer_comparison,
    validate_report_language,
)


def test_yoy_and_peg_are_calculated_for_byd():
    metrics = calculate_metrics("002594.SZ")
    assert metrics.revenue_yoy is not None
    assert metrics.revenue_yoy > 0
    assert metrics.peg is not None
    assert metrics.data_quality_score > 0


def test_peer_medians_ignore_unavailable_values():
    peers = get_peer_comparison("TSLA")
    assert peers.medians["pe"] is not None
    assert peers.medians["ev_ebitda"] is not None
    assert peers.premium_discount["pe"] is not None


def test_dcf_requires_discount_above_terminal_growth():
    assumptions = DcfAssumptions(discount_rate=0.02, terminal_growth_rate=0.03)
    try:
        calculate_dcf("TSLA", assumptions)
    except ValueError as exc:
        assert "Discount rate" in str(exc)
    else:
        raise AssertionError("Expected invalid DCF assumptions to fail")


def test_dcf_outputs_scenarios_and_sensitivity():
    result = calculate_dcf("TSLA")
    assert result.fair_value_per_share > 0
    assert {item.name for item in result.scenarios} == {"bear", "base", "bull"}
    assert len(result.sensitivity) == 3


def test_report_language_guardrails():
    report = build_report("TSLA")
    assert "not personalized investment advice" in report.disclaimer
    assert validate_report_language(report) == []
    assert report.sections[0].sources

