from ciscoconfparse2.models_cisco import IOSCfgLine

from c3.types import (
    ConditionBlock,
)


def evaluate_condition_block(
    obj: IOSCfgLine,
    condition_block: ConditionBlock,
) -> bool:
    """Determine whether a config object satisfies a conditions block.

    Used to filter which scope objects a rule applies to. An empty or absent
    conditions block matches every object. Within each key:
        - ``all``: every entry must match (pattern present / not_pattern absent).
        - ``any``: at least one entry must match.

    Both ``all`` and ``any`` may be present; both must pass for the object to
    be considered in scope.

    Args:
        obj (IOSCfgLine): The config line object whose children are searched.
        condition_block (ConditionBlock): Mapping with optional "all" and "any"
            keys, each containing a list of PatternCondition dicts.

    Returns:
        bool: True if the object satisfies all conditions, False otherwise.
    """

    if not condition_block:
        return True

    #
    # ALL
    #
    if "all" in condition_block:

        for condition in condition_block["all"]:

            if "pattern" in condition:

                if not obj.find_child_objects(
                    condition["pattern"]
                ):
                    return False

            if "not_pattern" in condition:

                if obj.find_child_objects(
                    condition["not_pattern"]
                ):
                    return False

    #
    # ANY
    #
    if "any" in condition_block:

        matched = False

        for condition in condition_block["any"]:

            if "pattern" in condition:

                if obj.find_child_objects(
                    condition["pattern"]
                ):
                    matched = True

            if "not_pattern" in condition:

                if not obj.find_child_objects(
                    condition["not_pattern"]
                ):
                    matched = True

        if not matched:
            return False

    return True