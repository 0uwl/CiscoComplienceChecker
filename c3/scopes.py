from ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.models_cisco import IOSCfgLine


def get_scope_objects(
    parse: CiscoConfParse,
    scope: str,
) -> list[IOSCfgLine]:
    """Return the top-level config objects that fall within the given scope.

    Named scopes map to fixed regex anchors; any other value is treated as a
    literal regex prefix anchored to the start of the line.

    Named scopes:
        - "global"     → lines matching ``^hostname``
        - "interfaces" → lines matching ``^interface ``
        - "vty"        → lines matching ``^line vty``
        - <other>      → lines matching ``^<scope>``

    Args:
        parse (CiscoConfParse): Parsed representation of the IOS config file.
        scope (str): Scope name or arbitrary regex prefix.

    Returns:
        list[IOSCfgLine]: Matching top-level config line objects.
    """

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