# Re-inspection Decision Agent

A lightweight, deterministic decision engine for multi-pass inspection workflows.

## Quick Start

```python
from reinspection_agent import ReinspectionDecisionAgent

agent = ReinspectionDecisionAgent()
result = agent.decide(
    zones_inspected=["Zone A", "Zone B"],
    zone_results=[
        {"zone": "Zone A", "risk_level": "low", "re_inspect_recommended": False, "detection_count": 0, "pass_number": 1},
        {"zone": "Zone B", "risk_level": "critical", "re_inspect_recommended": True, "detection_count": 5, "pass_number": 1},
    ],
    max_passes_allowed=3,
)
print(result.decision)  # DecisionType.REINSPECT
```

See [full documentation](README.md) for details.
