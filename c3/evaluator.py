from ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.models_cisco import IOSCfgLine

from c3.conditions import (
    evaluate_condition_block,
)

from c3.scopes import (
    get_scope_objects,
)

from c3.types import (
    MatchBlock,
    Rule,
    Violation,
)


def evaluate_match_block(
    obj: IOSCfgLine,
    match_block: MatchBlock,
    policy_type: str,
) -> bool:

    #
    # REQUIRED
    #
    if policy_type == "required":

        if "all" in match_block:

            for item in match_block["all"]:
                pattern = item.get("pattern")

                if pattern is not None:
                    return len(obj.find_child_objects(pattern)) > 0

            return True

        if "any" in match_block:

            for item in match_block["any"]:
                pattern = item.get("pattern")

                if pattern is not None:
                    return len(obj.find_child_objects(pattern)) > 0

            return False

    #
    # FORBIDDEN
    #
    elif policy_type == "forbidden":

        if "all" in match_block:

            for item in match_block["all"]:
                pattern = item.get("pattern")

                if pattern is not None:
                    return len(obj.find_child_objects(pattern)) > 0

            return True

        if "any" in match_block:

            for item in match_block["any"]:
                pattern = item.get("pattern")

                if pattern is not None:
                    return len(obj.find_child_objects(pattern)) > 0

            return True

    return True


def evaluate_rule(
    parse: CiscoConfParse,
    rule: Rule,
) -> list[Violation]:

    violations: list[Violation] = []

    scope_objects = get_scope_objects(
        parse,
        rule.scope,
    )

    for obj in scope_objects:

        if not evaluate_condition_block(
            obj,
            rule.conditions,
        ):
            continue

        compliant = evaluate_match_block(
            obj,
            rule.match,
            rule.policy_type,
        )

        if not compliant:

            violations.append(
                Violation(
                    rule=rule.rule_name,
                    severity=rule.severity,
                    message=rule.message,
                    example=rule.example,
                    scope=obj.text,
                )
            )

    return violations