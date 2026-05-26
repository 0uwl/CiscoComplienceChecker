#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from ciscoconfparse2 import CiscoConfParse

from c3.loader import load_policies
from c3.evaluator import evaluate_rule


def evaluate_config(config_file, policy_file):

    parse = CiscoConfParse(str(config_file))

    rules = load_policies(policy_file)

    violations = []

    for rule in rules:

        violations.extend(
            evaluate_rule(parse, rule)
        )

    score = 100

    overall_status = "ok"

    for violation in violations:

        score -= violation["score_impact"]

        if violation["severity"] == "critical":
            overall_status = "critical"

        elif (
            violation["severity"] == "warning"
            and overall_status != "critical"
        ):
            overall_status = "warning"

    score = max(score, 0)

    result = {
        "device": config_file.stem,
        "status": overall_status,
        "score": score,
        "violations": violations,
    }

    return result


def main():

    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} "
            "<config> <policy>"
        )
        sys.exit(1)

    config_file = Path(sys.argv[1])

    policy_file = Path(sys.argv[2])

    result = evaluate_config(
        config_file,
        policy_file,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()