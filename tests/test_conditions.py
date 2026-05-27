from ciscoconfparse2 import CiscoConfParse

from c3.conditions import (
    evaluate_condition_block,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _iface(*child_lines):
    """Return a parsed interface object with the given child lines."""
    config = CiscoConfParse(["interface GigabitEthernet0/1"] + list(child_lines))
    return config.find_objects(r"^interface")[0]


CLIENT_CONDITIONS = {
    "all": [{"not_pattern": r"^ description .*\(no sticky\).*"}],
    "any": [
        {"pattern": r"^ description .*[Cc]lient.*"},
        {"pattern": r"^ description .*[Aa]ccess.*"},
    ],
}

# ── existing: all with pattern ────────────────────────────────────────────────

def test_condition_match(
    compliant_config,
):

    interface = compliant_config.find_objects(
        r"^interface"
    )[0]

    condition_block = {
        "all": [
            {
                "pattern":
                    r"^ description .*"
            }
        ]
    }

    assert evaluate_condition_block(
        interface,
        condition_block,
    )


def test_condition_not_match(
    compliant_config,
):

    interface = compliant_config.find_objects(
        r"^interface"
    )[0]

    condition_block = {
        "all": [
            {
                "pattern":
                    r"^ shutdown$"
            }
        ]
    }

    assert (
        evaluate_condition_block(
            interface,
            condition_block,
        )
        is False
    )


# ── not_pattern ───────────────────────────────────────────────────────────────

def test_not_pattern_fails_when_present():
    # not_pattern IS found → condition fails
    iface = _iface(" description Client (no sticky) vlan 100")
    assert evaluate_condition_block(
        iface,
        {"all": [{"not_pattern": r"^ description .*\(no sticky\).*"}]},
    ) is False


def test_not_pattern_passes_when_absent():
    # not_pattern is NOT found → condition passes
    iface = _iface(" description Client access vlan 100")
    assert evaluate_condition_block(
        iface,
        {"all": [{"not_pattern": r"^ description .*\(no sticky\).*"}]},
    ) is True


# ── any ───────────────────────────────────────────────────────────────────────

def test_any_matches_first_pattern():
    iface = _iface(" description Client access vlan 100")
    assert evaluate_condition_block(
        iface,
        {"any": [
            {"pattern": r"^ description .*[Cc]lient.*"},
            {"pattern": r"^ description .*[Aa]ccess.*"},
        ]},
    ) is True


def test_any_matches_second_pattern():
    # "Access" doesn't match [Cc]lient but does match [Aa]ccess
    iface = _iface(" description Access port vlan 200")
    assert evaluate_condition_block(
        iface,
        {"any": [
            {"pattern": r"^ description .*[Cc]lient.*"},
            {"pattern": r"^ description .*[Aa]ccess.*"},
        ]},
    ) is True


def test_any_fails_when_no_pattern_matches():
    iface = _iface(" description Server trunk")
    assert evaluate_condition_block(
        iface,
        {"any": [
            {"pattern": r"^ description .*[Cc]lient.*"},
            {"pattern": r"^ description .*[Aa]ccess.*"},
        ]},
    ) is False


# ── combined all + any ────────────────────────────────────────────────────────

def test_all_and_any_both_pass():
    # not_pattern absent (passes all), Client matches (passes any)
    iface = _iface(" description Client access vlan 100")
    assert evaluate_condition_block(iface, CLIENT_CONDITIONS) is True


def test_all_fails_blocks_when_any_would_pass():
    # not_pattern present → all fails → False, even though Client matches any
    iface = _iface(" description Client (no sticky) vlan 100")
    assert evaluate_condition_block(iface, CLIENT_CONDITIONS) is False


def test_any_fails_in_combined_block():
    # not_pattern absent (passes all), but no Client/Access description (fails any)
    iface = _iface(" description Server trunk")
    assert evaluate_condition_block(iface, CLIENT_CONDITIONS) is False


# ── edge: empty conditions ────────────────────────────────────────────────────

def test_empty_conditions_always_pass():
    iface = _iface(" description anything at all")
    assert evaluate_condition_block(iface, {}) is True
