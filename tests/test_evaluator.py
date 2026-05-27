import pytest

from c3.evaluator import (
    evaluate_rule,
)


def _rule(interface_rules, name):
    return next(r for r in interface_rules if r.rule_name == name)


# ── existing ──────────────────────────────────────────────────────────────────

def test_compliant_rule(
    compliant_config,
    rules,
):

    aaa_rule = next(
        r
        for r in rules
        if r.rule_name == "aaa-model"
    )

    violations = evaluate_rule(
        compliant_config,
        aaa_rule,
    )

    assert violations == []


def test_telnet_violation(
    telnet_config,
    rules,
):

    aaa_rule = next(
        r
        for r in rules
        if r.rule_name == "no-telnet"
    )

    violations = evaluate_rule(
        telnet_config,
        aaa_rule,
    )

    assert len(violations) == 1

    violation = violations[0]

    assert violation.rule == "no-telnet"

    assert (
        violation.severity.value
        == "critical"
    )


# ── client_access ─────────────────────────────────────────────────────────────

def test_client_access_compliant(
    client_access_compliant_config,
    interface_rules,
):
    # All 6 required patterns present, Client description → no violation
    violations = evaluate_rule(
        client_access_compliant_config,
        _rule(interface_rules, "client_access"),
    )
    assert violations == []


def test_client_access_violation_missing_patterns(
    client_access_ports_config,
    interface_rules,
):
    # Client description present but port-security patterns missing → violation
    violations = evaluate_rule(
        client_access_ports_config,
        _rule(interface_rules, "client_access"),
    )
    assert len(violations) == 1
    assert violations[0].rule == "client_access"
    assert violations[0].severity.value == "warning"


def test_client_access_skipped_by_not_pattern(
    client_no_sticky_config,
    interface_rules,
):
    # "(no sticky)" in description triggers not_pattern → condition fails → skipped
    violations = evaluate_rule(
        client_no_sticky_config,
        _rule(interface_rules, "client_access"),
    )
    assert violations == []


def test_client_access_any_second_pattern(
    access_desc_compliant_config,
    interface_rules,
):
    # "Access" description: doesn't match [Cc]lient but matches [Aa]ccess → evaluated → compliant
    violations = evaluate_rule(
        access_desc_compliant_config,
        _rule(interface_rules, "client_access"),
    )
    assert violations == []


def test_client_access_skipped_when_no_matching_description(
    telnet_config,
    interface_rules,
):
    # telnet.cfg has description "UNUSED" — matches neither Client nor Access → skipped
    violations = evaluate_rule(
        telnet_config,
        _rule(interface_rules, "client_access"),
    )
    assert violations == []


# ── protected_port ────────────────────────────────────────────────────────────

def test_protected_port_compliant(
    protected_compliant_config,
    interface_rules,
):
    # (protected) description + switchport protected → no violation
    violations = evaluate_rule(
        protected_compliant_config,
        _rule(interface_rules, "protected_port"),
    )
    assert violations == []


def test_protected_port_violation(
    protected_violation_config,
    interface_rules,
):
    # (protected) description but switchport protected missing → violation
    violations = evaluate_rule(
        protected_violation_config,
        _rule(interface_rules, "protected_port"),
    )
    assert len(violations) == 1
    assert violations[0].rule == "protected_port"


def test_protected_port_skipped_when_not_marked(
    compliant_config,
    interface_rules,
):
    # No (protected) in description → condition fails → skipped
    violations = evaluate_rule(
        compliant_config,
        _rule(interface_rules, "protected_port"),
    )
    assert violations == []


# ── unused_port ───────────────────────────────────────────────────────────────

def test_unused_port_violation(
    unused_violation_config,
    interface_rules,
):
    # shutdown present, no vlan 4000 → condition passes → missing required patterns → violation
    violations = evaluate_rule(
        unused_violation_config,
        _rule(interface_rules, "unused_port"),
    )
    assert len(violations) == 1
    assert violations[0].rule == "unused_port"


def test_unused_port_skipped_when_vlan_already_set(
    unused_skipped_config,
    interface_rules,
):
    # shutdown + vlan 4000 present → not_pattern fires → condition fails → skipped
    violations = evaluate_rule(
        unused_skipped_config,
        _rule(interface_rules, "unused_port"),
    )
    assert violations == []


def test_unused_port_skipped_when_not_shutdown(
    client_access_compliant_config,
    interface_rules,
):
    # No shutdown line → condition pattern fails → skipped
    violations = evaluate_rule(
        client_access_compliant_config,
        _rule(interface_rules, "unused_port"),
    )
    assert violations == []
