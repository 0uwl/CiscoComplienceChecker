import yaml

from c3.types import (
    Rule,
    Severity,
)


def load_rules(
    policy_file: str,
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
                    conditions=rule_data.get(
                        "conditions",
                        {},
                    ),
                    match=rule_data.get(
                        "match",
                        {},
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