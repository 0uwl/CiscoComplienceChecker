#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from ciscoconfparse2 import CiscoConfParse

from c3.loader import load_rules
from c3.evaluator import evaluate_rule
from c3.types import ComplianceReport, Violation, Severity, SEVERITY_WEIGHTS
from typing import Literal


def evaluate_config(config_file: Path, policy_file: Path) -> ComplianceReport:
    parse = CiscoConfParse(str(config_file))

    rules = load_rules(policy_file)

    violations: list[Violation] = []

    for rule in rules:

        violations.extend(
            evaluate_rule(parse, rule)
        )

    overall_status: Literal["ok", "warning", "critical"] = "ok"

    for violation in violations:

        if violation.severity == Severity.CRITICAL:
            overall_status = "critical"

        elif (
            violation.severity == Severity.WARNING
            and overall_status != "critical"
        ):
            overall_status = "warning"

    score = max(0, 100 - sum(SEVERITY_WEIGHTS[v.severity] for v in violations))

    return ComplianceReport(
        device=config_file.stem,
        score=score,
        status=overall_status,
        violations=[v.to_dict() for v in violations],
    )


def scan_directory(dir_path: Path, policy_file: Path) -> list[ComplianceReport]:
    cfg_files = sorted(Path(dir_path).glob("*.cfg"))
    return [evaluate_config(cfg, policy_file) for cfg in cfg_files]


def _worst_exit_code(results: list[ComplianceReport]) -> int:
    statuses = {r["status"] for r in results}
    if "critical" in statuses:
        return 2
    if "warning" in statuses:
        return 1
    return 0


def main():
    """Entry point for the CLI."""

    parser = argparse.ArgumentParser(
        prog="c3",
        description="Cisco Compliance Checker",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        help="scan every .cfg file in PATH instead of a single config",
    )
    parser.add_argument("positional", nargs="*", metavar="ARG")

    args = parser.parse_args()

    if args.dir:
        if len(args.positional) != 1:
            parser.error("with --dir, provide exactly one argument: <policy.yml>")
        policy_file = Path(args.positional[0])
        dir_path = Path(args.dir)
        results = scan_directory(dir_path, policy_file)
        print(json.dumps(results, indent=2))
        sys.exit(_worst_exit_code(results))
    else:
        if len(args.positional) != 2:
            parser.error("provide <config.cfg> <policy.yml>")
        config_file = Path(args.positional[0])
        policy_file = Path(args.positional[1])
        result = evaluate_config(config_file, policy_file)
        print(json.dumps(result, indent=2))
        exit_codes = {"ok": 0, "warning": 1, "critical": 2}
        sys.exit(exit_codes[result["status"]])


if __name__ == "__main__":
    main()
