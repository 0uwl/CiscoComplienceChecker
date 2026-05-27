from dataclasses import dataclass, asdict
from enum import Enum
from typing import TypedDict, Literal, Any


#
# Severity levels
#

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


SEVERITY_WEIGHTS: dict["Severity", int] = {
    Severity.CRITICAL: 100,
    Severity.WARNING: 10,
    Severity.INFO: 0,
}


#
# Policy type
#

PolicyType = Literal["required", "forbidden"]


#
# Condition definitions from YAML
#

class PatternCondition(TypedDict, total=False):
    pattern: str
    not_pattern: str


class MatchBlock(TypedDict, total=False):
    all: list[PatternCondition]
    any: list[PatternCondition]


class ConditionBlock(TypedDict, total=False):
    all: list[PatternCondition]
    any: list[PatternCondition]


#
# Runtime normalized rule
#

@dataclass(slots=True)
class Rule:
    policy_type: PolicyType
    policy_name: str
    rule_name: str

    scope: str

    severity: Severity

    conditions: ConditionBlock
    match: MatchBlock

    message: str
    example: str


#
# Violation object
#

@dataclass(slots=True)
class Violation:
    rule: str
    severity: Severity

    message: str
    example: str

    scope: str
    
    def to_dict(self) -> "ViolationDict":
        return asdict(self)  # type: ignore[return-value]


#
# Serialised report types
#

class ViolationDict(TypedDict):
    rule: str
    severity: str
    message: str
    example: str
    scope: str


class ComplianceReport(TypedDict):
    device: str
    score: int
    status: Literal["ok", "warning", "critical"]
    violations: list[ViolationDict]


#
# Final compliance result
#

@dataclass(slots=True)
class ComplianceResult:
    device: str

    score: int

    status: Severity | Literal["ok"]

    violations: list[Violation]
