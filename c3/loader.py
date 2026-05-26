import yaml

from c3.types import (
    Rule,
    Severity,
)


def load_policies(
    policy_file: str,
) -> list[Rule]:

    with open(policy_file) as f:
        raw = yaml.safe_load(f)

    rules: list[Rule] = []

    policies = raw.get("policies", {})

    for policy_type, policy_groups in policies.items():

        for policy_name, policy_data in policy_groups.items():

            scope = policy_data["scope"]

            for rule_entry in policy_data.get("rules", []):

                rule_name = list(
                    rule_entry.keys()
                )[0]

                rule_data = rule_entry[rule_name]

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