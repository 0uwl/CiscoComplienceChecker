from ciscoconfparse2.models_cisco import IOSCfgLine

from c3.types import (
    ConditionBlock,
)


def evaluate_condition_block(
    obj: IOSCfgLine,
    condition_block: ConditionBlock,
) -> bool:

    if not condition_block:
        return True

    #
    # ALL
    #
    if "all" in condition_block:

        for condition in condition_block["all"]:

            if "pattern" in condition:

                if not obj.re_search_children(
                    condition["pattern"]
                ):
                    return False

            if "not_pattern" in condition:

                if obj.re_search_children(
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

                if obj.re_search_children(
                    condition["pattern"]
                ):
                    matched = True

            if "not_pattern" in condition:

                if not obj.re_search_children(
                    condition["not_pattern"]
                ):
                    matched = True

        if not matched:
            return False

    return True