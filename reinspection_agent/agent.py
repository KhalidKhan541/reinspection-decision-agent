from typing import Dict, List, Optional

from .exceptions import InvalidZoneDataError
from .models import DecisionOutput, DecisionType, RiskLevel, ZoneResult


class ReinspectionDecisionAgent:
    """
    Re-inspection Decision Agent.

    After each inspection cycle, decides whether additional passes are needed
    before the final report is generated.

    Decision Rules:
        1. If any zone has risk_level == "critical" AND pass_number < max_passes
           → re_inspect
        2. If re_inspect_recommended == True AND pass_number == 1
           → re_inspect that zone
        3. If pass_number >= max_passes → proceed_to_report regardless
        4. If all zones are "clear" or "low" → proceed_to_report immediately
        5. Never re-inspect "clear" or "low" zones — only medium and above
    """

    MIN_REINSPECT_RISK = RiskLevel.MEDIUM

    def decide(
        self,
        zones_inspected: List[str],
        zone_results: List[Dict],
        max_passes_allowed: int,
        re_inspect_threshold: str = "medium",
    ) -> DecisionOutput:
        """
        Decide whether to re-inspect or proceed to final report.

        Args:
            zones_inspected: List of zone identifiers that were inspected.
            zone_results: Per-zone inspection result dictionaries.
            max_passes_allowed: Maximum inspection passes before forced proceed.
            re_inspect_threshold: Minimum risk level to trigger re-inspection.

        Returns:
            DecisionOutput with decision, zones, reason, and instructions.

        Raises:
            InvalidZoneDataError: If zone_results contain invalid data.
        """
        self._validate_inputs(
            zones_inspected, zone_results, max_passes_allowed, re_inspect_threshold
        )

        threshold = RiskLevel(re_inspect_threshold)
        parsed_results = [self._parse_zone_result(r) for r in zone_results]

        zones_for_reinspection: List[str] = []
        pass_instructions: Dict[str, str] = {}
        reasons: List[str] = []

        for result in parsed_results:
            if self._should_skip_zone(result):
                continue

            if self._should_force_proceed(result, max_passes_allowed):
                continue

            if self._should_reinspect_critical(result, max_passes_allowed):
                self._add_reinspection(
                    result, zones_for_reinspection, pass_instructions, reasons
                )
                continue

            if self._should_reinspect_pass1(result, threshold):
                self._add_reinspection(
                    result, zones_for_reinspection, pass_instructions, reasons
                )
                continue

            if self._should_reinspect_threshold(result, threshold):
                self._add_reinspection(
                    result, zones_for_reinspection, pass_instructions, reasons
                )

        if zones_for_reinspection:
            return DecisionOutput(
                decision=DecisionType.REINSPECT,
                zones_for_reinspection=zones_for_reinspection,
                reason="; ".join(reasons) if reasons else "Zones require re-inspection",
                pass_instructions=pass_instructions,
            )

        return DecisionOutput(
            decision=DecisionType.PROCEED,
            reason=self._build_proceed_reason(parsed_results, max_passes_allowed),
        )

    def _validate_inputs(
        self,
        zones_inspected: List[str],
        zone_results: List[Dict],
        max_passes_allowed: int,
        re_inspect_threshold: str,
    ) -> None:
        if max_passes_allowed < 1:
            raise InvalidZoneDataError("max_passes_allowed must be at least 1")

        try:
            RiskLevel(re_inspect_threshold)
        except ValueError:
            raise InvalidZoneDataError(
                f"Invalid re_inspect_threshold: {re_inspect_threshold}"
            )

        if not zone_results:
            raise InvalidZoneDataError("zone_results cannot be empty")

        for result in zone_results:
            if "zone" not in result:
                raise InvalidZoneDataError("Each zone result must have a 'zone' field")
            if "risk_level" not in result:
                raise InvalidZoneDataError(
                    f"Zone {result.get('zone', '?')} missing 'risk_level'"
                )
            try:
                RiskLevel(result["risk_level"])
            except ValueError:
                raise InvalidZoneDataError(
                    f"Zone {result['zone']} has invalid risk_level: {result['risk_level']}"
                )

    def _parse_zone_result(self, raw: Dict) -> ZoneResult:
        return ZoneResult(
            zone=raw["zone"],
            risk_level=RiskLevel(raw["risk_level"]),
            re_inspect_recommended=bool(raw.get("re_inspect_recommended", False)),
            detection_count=int(raw.get("detection_count", 0)),
            pass_number=int(raw.get("pass_number", 1)),
            re_inspect_reason=raw.get("re_inspect_reason"),
        )

    def _should_skip_zone(self, result: ZoneResult) -> bool:
        """Rule 5: Never re-inspect clear or low zones."""
        return result.risk_level in (RiskLevel.CLEAR, RiskLevel.LOW)

    def _should_force_proceed(self, result: ZoneResult, max_passes: int) -> bool:
        """Rule 3: If pass_number >= max_passes → proceed regardless."""
        return result.pass_number >= max_passes

    def _should_reinspect_critical(
        self, result: ZoneResult, max_passes: int
    ) -> bool:
        """Rule 1: Critical zone with passes remaining → re-inspect."""
        return result.risk_level == RiskLevel.CRITICAL and result.pass_number < max_passes

    def _should_reinspect_pass1(self, result: ZoneResult, threshold: RiskLevel) -> bool:
        """Rule 2: re_inspect_recommended on pass 1 at or above threshold."""
        return (
            result.re_inspect_recommended
            and result.pass_number == 1
            and result.risk_level >= threshold
        )

    def _should_reinspect_threshold(self, result: ZoneResult, threshold: RiskLevel) -> bool:
        """Additional rule: re_inspect_recommended at or above threshold."""
        return result.re_inspect_recommended and result.risk_level >= threshold

    def _add_reinspection(
        self,
        result: ZoneResult,
        zones: List[str],
        instructions: Dict[str, str],
        reasons: List[str],
    ) -> None:
        if result.zone not in zones:
            zones.append(result.zone)
            instructions[result.zone] = self._generate_instruction(result)
            reasons.append(self._build_zone_reason(result))

    def _generate_instruction(self, result: ZoneResult) -> str:
        if result.re_inspect_reason:
            return f"Re-inspect {result.zone}: {result.re_inspect_reason}. Increase detection sensitivity."
        if result.risk_level == RiskLevel.CRITICAL:
            return (
                f"Critical findings in {result.zone}. "
                "Perform thorough re-inspection with elevated sensitivity."
            )
        if result.risk_level == RiskLevel.HIGH:
            return (
                f"High-risk indicators in {result.zone}. "
                "Re-inspect with increased detection sensitivity."
            )
        return f"Medium-risk indicators in {result.zone}. Perform follow-up inspection."

    def _build_zone_reason(self, result: ZoneResult) -> str:
        if result.risk_level == RiskLevel.CRITICAL:
            return f"{result.zone} is critical (pass {result.pass_number})"
        return (
            f"{result.zone} is {result.risk_level.value} "
            f"with re-inspection recommended (pass {result.pass_number})"
        )

    def _build_proceed_reason(
        self, results: List[ZoneResult], max_passes: int
    ) -> str:
        if not results:
            return "No zones inspected. Proceeding to report."

        all_clear = all(r.risk_level in (RiskLevel.CLEAR, RiskLevel.LOW) for r in results)
        if all_clear:
            return "All zones are clear or low risk. No additional inspection needed."

        at_max = any(r.pass_number >= max_passes for r in results)
        if at_max:
            return (
                f"Maximum inspection passes ({max_passes}) reached. "
                "Proceeding to final report."
            )

        return "No zones require re-inspection. Proceeding to final report."
