import pytest
from reinspection_agent import ReinspectionDecisionAgent, RiskLevel, DecisionType


@pytest.fixture
def agent():
    return ReinspectionDecisionAgent()


class TestDecisionRules:
    """Tests for the 5 core decision rules."""

    def test_rule1_critical_reinspects_when_passes_remaining(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": False,
                 "detection_count": 5, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.REINSPECT
        assert "A" in result.zones_for_reinspection

    def test_rule1_critical_proceeds_at_max_passes(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": True,
                 "detection_count": 5, "pass_number": 3}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED

    def test_rule2_reinspect_recommended_on_pass1(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "high", "re_inspect_recommended": True,
                 "re_inspect_reason": "Crack detected", "detection_count": 2, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.REINSPECT
        assert "A" in result.zones_for_reinspection
        assert "Crack detected" in result.pass_instructions["A"]

    def test_rule2_no_reinspect_on_pass2(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "high", "re_inspect_recommended": True,
                 "detection_count": 2, "pass_number": 2}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED

    def test_rule3_max_passes_forces_proceed(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": True,
                 "detection_count": 10, "pass_number": 5}
            ],
            max_passes_allowed=5,
        )
        assert result.decision == DecisionType.PROCEED
        assert result.zones_for_reinspection == []

    def test_rule4_all_clear_proceeds(self, agent):
        result = agent.decide(
            zones_inspected=["A", "B", "C"],
            zone_results=[
                {"zone": "A", "risk_level": "clear", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1},
                {"zone": "B", "risk_level": "clear", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1},
                {"zone": "C", "risk_level": "low", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1},
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED

    def test_rule4_all_low_proceeds(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "low", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED

    def test_rule5_clear_zone_never_reinspected(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "clear", "re_inspect_recommended": True,
                 "detection_count": 0, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED
        assert "A" not in result.zones_for_reinspection

    def test_rule5_low_zone_never_reinspected(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "low", "re_inspect_recommended": True,
                 "detection_count": 0, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.PROCEED
        assert "A" not in result.zones_for_reinspection


class TestMultiZoneScenarios:
    """Tests for complex multi-zone decision scenarios."""

    def test_mixed_risks_some_reinspect(self, agent):
        result = agent.decide(
            zones_inspected=["A", "B", "C"],
            zone_results=[
                {"zone": "A", "risk_level": "low", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1},
                {"zone": "B", "risk_level": "critical", "re_inspect_recommended": True,
                 "re_inspect_reason": "Structural damage", "detection_count": 5, "pass_number": 1},
                {"zone": "C", "risk_level": "medium", "re_inspect_recommended": True,
                 "re_inspect_reason": "Surface anomaly", "detection_count": 1, "pass_number": 1},
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.REINSPECT
        assert "B" in result.zones_for_reinspection
        assert "C" in result.zones_for_reinspection
        assert "A" not in result.zones_for_reinspection

    def test_no_duplicate_zones_in_reinspection(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": True,
                 "detection_count": 5, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.zones_for_reinspection.count("A") == 1

    def test_threshold_respected(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "medium", "re_inspect_recommended": True,
                 "detection_count": 1, "pass_number": 1}
            ],
            max_passes_allowed=3,
            re_inspect_threshold="high",
        )
        assert result.decision == DecisionType.PROCEED

    def test_threshold_exact_match(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "high", "re_inspect_recommended": True,
                 "detection_count": 2, "pass_number": 1}
            ],
            max_passes_allowed=3,
            re_inspect_threshold="high",
        )
        assert result.decision == DecisionType.REINSPECT


class TestPassInstructions:
    """Tests for generated pass instructions."""

    def test_critical_instruction(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": False,
                 "detection_count": 5, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert "Critical findings" in result.pass_instructions["A"]
        assert "elevated sensitivity" in result.pass_instructions["A"]

    def test_high_instruction(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "high", "re_inspect_recommended": True,
                 "re_inspect_reason": "Crack pattern", "detection_count": 2, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert "Crack pattern" in result.pass_instructions["A"]

    def test_medium_instruction(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "medium", "re_inspect_recommended": True,
                 "detection_count": 1, "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert "Medium-risk" in result.pass_instructions["A"]


class TestValidation:
    """Tests for input validation."""

    def test_empty_zone_results_raises(self, agent):
        from reinspection_agent.exceptions import InvalidZoneDataError
        with pytest.raises(InvalidZoneDataError):
            agent.decide(
                zones_inspected=["A"],
                zone_results=[],
                max_passes_allowed=3,
            )

    def test_invalid_risk_level_raises(self, agent):
        from reinspection_agent.exceptions import InvalidZoneDataError
        with pytest.raises(InvalidZoneDataError):
            agent.decide(
                zones_inspected=["A"],
                zone_results=[
                    {"zone": "A", "risk_level": "invalid", "re_inspect_recommended": False,
                     "detection_count": 0, "pass_number": 1}
                ],
                max_passes_allowed=3,
            )

    def test_zero_max_passes_raises(self, agent):
        from reinspection_agent.exceptions import InvalidZoneDataError
        with pytest.raises(InvalidZoneDataError):
            agent.decide(
                zones_inspected=["A"],
                zone_results=[
                    {"zone": "A", "risk_level": "low", "re_inspect_recommended": False,
                     "detection_count": 0, "pass_number": 1}
                ],
                max_passes_allowed=0,
            )

    def test_invalid_threshold_raises(self, agent):
        from reinspection_agent.exceptions import InvalidZoneDataError
        with pytest.raises(InvalidZoneDataError):
            agent.decide(
                zones_inspected=["A"],
                zone_results=[
                    {"zone": "A", "risk_level": "low", "re_inspect_recommended": False,
                     "detection_count": 0, "pass_number": 1}
                ],
                max_passes_allowed=3,
                re_inspect_threshold="invalid",
            )

    def test_missing_zone_field_raises(self, agent):
        from reinspection_agent.exceptions import InvalidZoneDataError
        with pytest.raises(InvalidZoneDataError):
            agent.decide(
                zones_inspected=["A"],
                zone_results=[
                    {"risk_level": "low", "re_inspect_recommended": False,
                     "detection_count": 0, "pass_number": 1}
                ],
                max_passes_allowed=3,
            )


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_single_zone_single_pass(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "medium", "re_inspect_recommended": False,
                 "detection_count": 0, "pass_number": 1}
            ],
            max_passes_allowed=1,
        )
        assert result.decision == DecisionType.PROCEED

    def test_optional_fields_default(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "high", "re_inspect_recommended": True,
                 "pass_number": 1}
            ],
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.REINSPECT

    def test_many_zones(self, agent):
        zones = [f"Zone_{i}" for i in range(20)]
        results = [
            {"zone": f"Zone_{i}", "risk_level": "clear", "re_inspect_recommended": False,
             "detection_count": 0, "pass_number": 1}
            for i in range(19)
        ] + [
            {"zone": "Zone_19", "risk_level": "critical", "re_inspect_recommended": True,
             "detection_count": 8, "pass_number": 1}
        ]
        result = agent.decide(
            zones_inspected=zones,
            zone_results=results,
            max_passes_allowed=3,
        )
        assert result.decision == DecisionType.REINSPECT
        assert "Zone_19" in result.zones_for_reinspection

    def test_reason_contains_pass_number(self, agent):
        result = agent.decide(
            zones_inspected=["A"],
            zone_results=[
                {"zone": "A", "risk_level": "critical", "re_inspect_recommended": False,
                 "detection_count": 3, "pass_number": 2}
            ],
            max_passes_allowed=5,
        )
        assert "pass 2" in result.reason
