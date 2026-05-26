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


def _find(
    parse: CiscoConfParse,
    obj: IOSCfgLine,
    pattern: str,
    scope: str,
) -> bool:
    """Search for a pattern, dispatching on scope.

    For the "global" scope, searches all top-level lines in the full parse
    because global config items are siblings of the hostname line, not
    children. For all other scopes, searches the child lines of the given
    config object.

    Args:
        parse (CiscoConfParse): Full parsed config, used for global lookups.
        obj (IOSCfgLine): Scope object whose children are searched for
            non-global scopes.
        pattern (str): Regex pattern to search for.
        scope (str): Scope name from the rule ("global", "interfaces", etc.).

    Returns:
        bool: True if at least one matching line is found, False otherwise.
    """
    if scope == "global":
        return len(parse.find_objects(pattern)) > 0
    return len(obj.find_child_objects(pattern)) > 0


def _check_all(
    parse: CiscoConfParse,
    obj: IOSCfgLine,
    items: list,
    scope: str,
) -> bool:
    """Return True if every item in the list satisfies its pattern conditions.

    For each item, a ``pattern`` must be present and a ``not_pattern`` must
    be absent. Any single failure causes an immediate False return.

    Args:
        parse (CiscoConfParse): Full parsed config, forwarded to ``_find``.
        obj (IOSCfgLine): Scope object being evaluated.
        items (list): List of PatternCondition dicts from the match block.
        scope (str): Scope name forwarded to ``_find``.

    Returns:
        bool: True if all items pass, False if any item fails.
    """
    for item in items:
        pattern = item.get("pattern")
        not_pattern = item.get("not_pattern")
        if pattern is not None and not _find(parse, obj, pattern, scope):
            return False
        if not_pattern is not None and _find(parse, obj, not_pattern, scope):
            return False
    return True


def _check_any(
    parse: CiscoConfParse,
    obj: IOSCfgLine,
    items: list,
    scope: str,
) -> bool:
    """Return True if at least one item in the list satisfies its pattern conditions.

    For each item, a ``pattern`` being present or a ``not_pattern`` being
    absent counts as a match. Returns True on the first match found.

    Args:
        parse (CiscoConfParse): Full parsed config, forwarded to ``_find``.
        obj (IOSCfgLine): Scope object being evaluated.
        items (list): List of PatternCondition dicts from the match block.
        scope (str): Scope name forwarded to ``_find``.

    Returns:
        bool: True if any item matches, False if none match.
    """
    for item in items:
        pattern = item.get("pattern")
        not_pattern = item.get("not_pattern")
        if pattern is not None and _find(parse, obj, pattern, scope):
            return True
        if not_pattern is not None and not _find(parse, obj, not_pattern, scope):
            return True
    return False


def evaluate_match_block(
    parse: CiscoConfParse,
    obj: IOSCfgLine,
    match_block: MatchBlock,
    policy_type: str,
    scope: str,
) -> bool:
    """Determine whether a config object is compliant with a match block.

    Evaluates ``all`` and ``any`` sub-blocks independently; when both are
    present, both must pass. The result is then interpreted by policy type:
        - ``required``: patterns must be present — a match means compliant.
        - ``forbidden``: patterns must be absent — a match means a violation.

    Both ``pattern`` and ``not_pattern`` are supported within each item.

    Args:
        parse (CiscoConfParse): Full parsed config, forwarded to ``_find``.
        obj (IOSCfgLine): The config object being evaluated.
        match_block (MatchBlock): Mapping with optional "all" and "any" keys,
            each containing a list of PatternCondition dicts.
        policy_type (str): Either "required" or "forbidden".
        scope (str): Scope name from the rule, forwarded to ``_find``.

    Returns:
        bool: True if the object is compliant, False if it is a violation.
    """
    if not match_block:
        return True

    matches = True

    if "all" in match_block:
        matches = _check_all(parse, obj, match_block["all"], scope)

    if matches and "any" in match_block:
        matches = _check_any(parse, obj, match_block["any"], scope)

    if policy_type == "forbidden":
        return not matches
    return matches


def evaluate_rule(
    parse: CiscoConfParse,
    rule: Rule,
) -> list[Violation]:
    """Evaluate a single rule against a parsed config and return all violations.

    Resolves the scope objects for the rule, filters them through the
    conditions block, then checks each surviving object against the match
    block. Objects that fail the match check produce a Violation.

    Args:
        parse (CiscoConfParse): Parsed representation of the IOS config file.
        rule (Rule): The normalised rule to evaluate.

    Returns:
        list[Violation]: All violations found for this rule. Empty list means
            the config is fully compliant with the rule.
    """
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
            parse,
            obj,
            rule.match,
            rule.policy_type,
            rule.scope,
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
