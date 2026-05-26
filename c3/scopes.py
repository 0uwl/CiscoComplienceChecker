from ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.models_cisco import IOSCfgLine


def get_scope_objects(
    parse: CiscoConfParse,
    scope: str,
) -> list[IOSCfgLine]:

    match scope:

        case "global":
            return parse.find_objects(
                r"^hostname"
            ) # type: ignore

        case "interfaces":
            return parse.find_objects(
                r"^interface "
            ) # type: ignore

        case "vty":
            return parse.find_objects(
                r"^line vty"
            ) # type: ignore

        case _:
            return parse.find_objects(
                rf"^{scope}"
            ) # type: ignore