from pathlib import Path

import yaml

from c3.types import (
    Rule,
    Severity,
)


def _add_child_indent(pattern: str) -> str:
    """Insert one space after a leading '^' if not already present.

    Child lines in IOS configs are indented by one space. Patterns anchored
    with '^' must therefore start with '^ ' to match. This function lets
    policy authors omit the space; the loader adds it automatically.
    Patterns that already have '^ ', use no '^' anchor, or are empty are
    returned unchanged.
    """
    if pattern.startswith("^") and not pattern.startswith("^ "):
        return "^ " + pattern[1:]
    return pattern


def _normalize_block(block: dict, add_indent: bool) -> dict:
    """Return a copy of a match/conditions block with child-line indentation applied.

    Walks every item in every 'all'/'any' list and passes 'pattern' and
    'not_pattern' values through _add_child_indent when add_indent is True.
    """
    if not block or not add_indent:
        return block
    result = {}
    for key, items in block.items():
        normalized = []
        for item in items:
            new_item = dict(item)
            if "pattern" in new_item:
                new_item["pattern"] = _add_child_indent(new_item["pattern"])
            if "not_pattern" in new_item:
                new_item["not_pattern"] = _add_child_indent(new_item["not_pattern"])
            normalized.append(new_item)
        result[key] = normalized
    return result


def load_rules(
    policy_file: Path | str,
) -> list[Rule]:
    """Load and normalise all rules from a YAML policy file.

    Reads the policy YAML and flattens the nested structure
    (policies → required|forbidden → policy_name → rules) into a flat list
    of Rule dataclass instances ready for evaluation.

    Args:
        policy_file (str): Path to the YAML policy file.

    Returns:
        list[Rule]: Flat list of normalised Rule instances.
    """

    with open(policy_file) as f:
        raw = yaml.safe_load(f)

    rules: list[Rule] = []

    policies = raw.get("policies", {})

    for policy_type, policy_groups in policies.items():

        for policy_name, policy_data in policy_groups.items():

            scope = policy_data["scope"]
            is_child_scope = scope != "global"

            for rule_name, rule_data in policy_data.get("rules", {}).items():

                rule = Rule(
                    policy_type=policy_type,
                    policy_name=policy_name,
                    rule_name=rule_name,
                    scope=scope,
                    severity=Severity(
                        rule_data.get(
                            "severity",
                            "warning",
                        )
                    ),
                    conditions=_normalize_block(
                        rule_data.get("conditions", {}),
                        add_indent=True,
                    ),
                    match=_normalize_block(
                        rule_data.get("match", {}),
                        add_indent=is_child_scope,
                    ),
                    message=rule_data.get(
                        "message",
                        "",
                    ),
                    example=rule_data.get(
                        "example",
                        "",
                    ),
                )

                rules.append(rule)

    return rules