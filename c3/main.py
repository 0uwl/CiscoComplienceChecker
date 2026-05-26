#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from ciscoconfparse2 import CiscoConfParse

from c3.loader import load_rules
from c3.evaluator import evaluate_rule
from c3.types import Violation, Severity, SEVERITY_WEIGHTS


def evaluate_config(config_file, policy_file):
    """Evaluate a Cisco IOS config file against a policy file.

    Parses the config, loads all rules from the policy, runs each rule through
    the evaluator, and aggregates the results into a compliance report.

    Args:
        config_file (Path): Path to the Cisco IOS .cfg file.
        policy_file (Path): Path to the YAML policy file.

    Returns:
        dict: Compliance report with keys:
            - device (str): Stem of the config filename.
            - status (str): Worst severity seen ("ok", "warning", or "critical").
            - violations (list[dict]): Serialised Violation instances.
    """

    parse = CiscoConfParse(str(config_file))

    rules = load_rules(policy_file)

    violations: list[Violation] = []

    for rule in rules:

        violations.extend(
            evaluate_rule(parse, rule)
        )

    overall_status = "ok"

    for violation in violations:

        if violation.severity == Severity.CRITICAL:
            overall_status = "critical"

        elif (
            violation.severity == Severity.WARNING
            and overall_status != "critical"
        ):
            overall_status = "warning"

    score = max(0, 100 - sum(SEVERITY_WEIGHTS[v.severity] for v in violations))

    result = {
        "device": config_file.stem,
        "score": score,
        "status": overall_status,
        "violations": [v.to_dict() for v in violations],
    }

    return result


def main():
    """Entry point for the CLI.

    Expects exactly two positional arguments: the path to a Cisco IOS config
    file and the path to a YAML policy file. Prints the compliance report as
    indented JSON to stdout.

    Returns:
        None
    """

    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} "
            "<config> <policy>"
        )
        sys.exit(64)

    config_file = Path(sys.argv[1])

    policy_file = Path(sys.argv[2])

    result = evaluate_config(
        config_file,
        policy_file,
    )

    print(json.dumps(result, indent=2))

    exit_codes = {"ok": 0, "warning": 1, "critical": 2}
    sys.exit(exit_codes[result["status"]])


if __name__ == "__main__":
    main()