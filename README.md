<div align="center">

# Re-inspection Decision Agent

**Autonomous decision engine for multi-pass inspection workflows**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

---

*A lightweight, deterministic agent that decides whether your inspection cycle needs another pass — or if you're ready for the final report.*

</div>

---

## What It Does

After each inspection cycle, this agent evaluates zone-level risk data and makes a binary decision:

```
re_inspect  →  "Zone B needs another pass. Focus on the northeast corner."
proceed_to_report  →  "All clear. Generate the final report."
```

No ML models. No external APIs. Pure logic, fast execution, full traceability.

---

## Decision Rules

The agent applies 5 rules in priority order:

| # | Rule | Trigger |
|---|------|---------|
| 1 | **Critical re-inspect** | `risk_level == "critical"` AND passes remaining |
| 2 | **Pass-1 re-inspect** | `re_inspect_recommended == true` on first pass |
| 3 | **Max passes forced** | `pass_number >= max_passes` → always proceed |
| 4 | **All clear** | Every zone is `clear` or `low` → proceed immediately |
| 5 | **Skip low-risk** | Never re-inspect `clear` or `low` zones |

---

## Quick Start

### Install

```bash
pip install reinspection-decision-agent
```

Or from source:

```bash
git clone https://github.com/KhalidKhan541/reinspection-decision-agent.git
cd reinspection-decision-agent
pip install -e .
```

### Use

```python
from reinspection_agent import ReinspectionDecisionAgent

agent = ReinspectionDecisionAgent()

result = agent.decide(
    zones_inspected=["Zone A", "Zone B", "Zone C"],
    zone_results=[
        {
            "zone": "Zone A",
            "risk_level": "low",
            "re_inspect_recommended": False,
            "detection_count": 0,
            "pass_number": 1,
        },
        {
            "zone": "Zone B",
            "risk_level": "critical",
            "re_inspect_recommended": True,
            "re_inspect_reason": "Structural crack detected",
            "detection_count": 5,
            "pass_number": 1,
        },
        {
            "zone": "Zone C",
            "risk_level": "medium",
            "re_inspect_recommended": True,
            "re_inspect_reason": "Surface discoloration",
            "detection_count": 1,
            "pass_number": 1,
        },
    ],
    max_passes_allowed=3,
    re_inspect_threshold="medium",
)

print(result.decision)        # DecisionType.REINSPECT
print(result.zones_for_reinspection)  # ["Zone B", "Zone C"]
print(result.pass_instructions)       # {"Zone B": "...", "Zone C": "..."}
```

---

## Output Schema

```python
@dataclass
class DecisionOutput:
    decision: DecisionType          # "proceed_to_report" | "re_inspect"
    zones_for_reinspection: List[str]
    reason: str
    pass_instructions: Dict[str, str]
```

### Example Output

```json
{
  "decision": "re_inspect",
  "zones_for_reinspection": ["Zone B", "Zone C"],
  "reason": "Zone B is critical (pass 1); Zone C is medium with re-inspection recommended (pass 1)",
  "pass_instructions": {
    "Zone B": "Re-inspect Zone B: Structural crack detected. Increase detection sensitivity.",
    "Zone C": "Medium-risk indicators in Zone C. Perform follow-up inspection."
  }
}
```

---

## Risk Levels

| Level | Re-inspectable | Description |
|-------|----------------|-------------|
| `clear` | No | No anomalies detected |
| `low` | No | Minor, non-actionable findings |
| `medium` | Yes | Actionable anomalies requiring follow-up |
| `high` | Yes | Significant risk indicators |
| `critical` | Yes | Severe risk, immediate attention required |

---

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `zones_inspected` | `List[str]` | — | Zone identifiers |
| `zone_results` | `List[Dict]` | — | Per-zone inspection data |
| `max_passes_allowed` | `int` | — | Max inspection passes |
| `re_inspect_threshold` | `str` | `"medium"` | Min risk level for re-inspection |

---

## Project Structure

```
reinspection-decision-agent/
├── reinspection_agent/
│   ├── __init__.py          # Public API exports
│   ├── agent.py             # Core decision logic
│   ├── models.py            # Data models and enums
│   └── exceptions.py        # Custom exceptions
├── tests/
│   ├── __init__.py
│   └── test_agent.py        # 25+ test cases
├── pyproject.toml           # Build config
├── LICENSE
└── README.md
```

---

## Testing

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=reinspection_agent --cov-report=term-missing
```

### Test Coverage

| Category | Tests |
|----------|-------|
| Core Decision Rules | 9 |
| Multi-Zone Scenarios | 4 |
| Pass Instructions | 3 |
| Input Validation | 5 |
| Edge Cases | 4 |
| **Total** | **25+** |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           ReinspectionDecisionAgent         │
├─────────────────────────────────────────────┤
│  Input                                     │
│  ├── zones_inspected: ["A", "B", "C"]      │
│  ├── zone_results: [...]                   │
│  ├── max_passes_allowed: 3                 │
│  └── re_inspect_threshold: "medium"        │
├─────────────────────────────────────────────┤
│  Decision Engine                           │
│  ├── Rule 5: Skip clear/low zones          │
│  ├── Rule 3: Force proceed at max passes   │
│  ├── Rule 1: Critical → re-inspect         │
│  ├── Rule 2: Pass-1 re-inspect             │
│  └── Rule Threshold: Above threshold       │
├─────────────────────────────────────────────┤
│  Output                                    │
│  ├── decision: proceed_to_report|re_inspect│
│  ├── zones_for_reinspection: [...]         │
│  ├── reason: "..."                         │
│  └── pass_instructions: {...}              │
└─────────────────────────────────────────────┘
```

---

## Use Cases

- **Infrastructure inspection** — bridges, buildings, roads
- **Manufacturing QA** — assembly line defect detection
- **Environmental monitoring** — multi-zone sensor networks
- **Security audits** — phased vulnerability assessments
- **Medical imaging** — multi-pass diagnostic analysis

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/add-new-rule`)
3. Commit your changes (`git commit -m 'feat: add new decision rule'`)
4. Push to the branch (`git push origin feat/add-new-rule`)
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with precision. Decided with confidence.**

</div>
