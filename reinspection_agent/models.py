from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RiskLevel(str, Enum):
    """Risk levels ordered from lowest to highest severity."""

    CLEAR = "clear"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def order(cls) -> List["RiskLevel"]:
        return [cls.CLEAR, cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL]

    def __ge__(self, other: "RiskLevel") -> bool:
        return self.order().index(self) >= self.order().index(other)

    def __gt__(self, other: "RiskLevel") -> bool:
        return self.order().index(self) > self.order().index(other)

    def __le__(self, other: "RiskLevel") -> bool:
        return self.order().index(self) <= self.order().index(other)

    def __lt__(self, other: "RiskLevel") -> bool:
        return self.order().index(self) < self.order().index(other)


class DecisionType(str, Enum):
    """Decision output types."""

    PROCEED = "proceed_to_report"
    REINSPECT = "re_inspect"


@dataclass
class ZoneResult:
    """Result from a single zone inspection."""

    zone: str
    risk_level: RiskLevel
    re_inspect_recommended: bool
    detection_count: int
    pass_number: int
    re_inspect_reason: Optional[str] = None


@dataclass
class DecisionOutput:
    """Structured output from the decision agent."""

    decision: DecisionType
    zones_for_reinspection: List[str] = field(default_factory=list)
    reason: str = ""
    pass_instructions: Dict[str, str] = field(default_factory=dict)
