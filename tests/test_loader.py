from pathlib import Path

import pytest

from c3.loader import _add_child_indent, _normalize_block, load_rules
from c3.types import Rule

FIXTURES = Path(__file__).parent / "fixtures" / "policies"


# ── existing ──────────────────────────────────────────────────────────────────

def test_policy_loader(rules):

    assert len(rules) == 9

    rule = rules[0]

    assert isinstance(rule, Rule)

    assert rule.rule_name == "aaa-model"

    assert rule.scope == "global"

    assert rule.severity.value == "warning"


# ── _add_child_indent ─────────────────────────────────────────────────────────

def test_indent_added_after_caret():
    assert _add_child_indent("^shutdown$") == "^ shutdown$"


def test_indent_not_duplicated_when_already_present():
    assert _add_child_indent("^ shutdown$") == "^ shutdown$"


def test_unanchored_pattern_unchanged():
    # No leading '^' — used as a substring search; leave as-is
    assert _add_child_indent("shutdown") == "shutdown"


def test_caret_only_gets_space():
    assert _add_child_indent("^") == "^ "


# ── _normalize_block ──────────────────────────────────────────────────────────

def test_normalize_block_adds_indent_to_pattern():
    block = {"all": [{"pattern": "^shutdown$"}]}
    result = _normalize_block(block, add_indent=True)
    assert result["all"][0]["pattern"] == "^ shutdown$"


def test_normalize_block_adds_indent_to_not_pattern():
    block = {"all": [{"not_pattern": "^shutdown$"}]}
    result = _normalize_block(block, add_indent=True)
    assert result["all"][0]["not_pattern"] == "^ shutdown$"


def test_normalize_block_skips_indent_when_disabled():
    block = {"all": [{"pattern": "^aaa new-model$"}]}
    result = _normalize_block(block, add_indent=False)
    assert result["all"][0]["pattern"] == "^aaa new-model$"


def test_normalize_block_handles_any_key():
    block = {"any": [{"pattern": "^description.*Client.*"}]}
    result = _normalize_block(block, add_indent=True)
    assert result["any"][0]["pattern"] == "^ description.*Client.*"


def test_normalize_block_empty_returns_unchanged():
    assert _normalize_block({}, add_indent=True) == {}


# ── integration: patterns in loaded rules ────────────────────────────────────

def test_global_scope_match_patterns_not_indented(rules):
    # Global scope searches top-level lines — no indent should be added
    aaa_rule = next(r for r in rules if r.rule_name == "aaa-model")
    pattern = aaa_rule.match["all"][0]["pattern"]
    assert pattern == "^aaa new-model$"


def test_child_scope_match_patterns_indented(rules):
    # Non-global match patterns must have '^ ' after normalization
    client_rule = next(r for r in rules if r.rule_name == "client_access")
    for item in client_rule.match["all"]:
        assert item["pattern"].startswith("^ "), (
            f"Expected '^ ' prefix on '{item['pattern']}'"
        )


def test_conditions_patterns_always_indented(rules):
    # Conditions always search child lines regardless of scope
    client_rule = next(r for r in rules if r.rule_name == "client_access")
    for item in client_rule.conditions.get("any", []):
        assert item["pattern"].startswith("^ ")


def test_conditions_not_pattern_indented(rules):
    client_rule = next(r for r in rules if r.rule_name == "client_access")
    not_pat = client_rule.conditions["all"][0]["not_pattern"]
    assert not_pat.startswith("^ ")


def test_vty_scope_match_patterns_indented(rules):
    exec_rule = next(r for r in rules if r.rule_name == "exec-timeout")
    pattern = exec_rule.match["all"][0]["pattern"]
    assert pattern.startswith("^ ")


# ── include ───────────────────────────────────────────────────────────────────

def test_include_merges_rules_from_base():
    rules = load_rules(FIXTURES / "child.yml")
    rule_names = [r.rule_name for r in rules]
    assert "aaa-model" in rule_names       # from base.yml
    assert "no-http-server" in rule_names  # defined in child.yml


def test_include_base_rules_come_first():
    rules = load_rules(FIXTURES / "child.yml")
    rule_names = [r.rule_name for r in rules]
    assert rule_names.index("aaa-model") < rule_names.index("no-http-server")


def test_include_base_only_loads_its_own_rules():
    rules = load_rules(FIXTURES / "base.yml")
    assert len(rules) == 1
    assert rules[0].rule_name == "aaa-model"


def test_circular_include_raises():
    with pytest.raises(ValueError, match="Circular include"):
        load_rules(FIXTURES / "circular_a.yml")


# ── override ──────────────────────────────────────────────────────────────────

def test_override_child_rule_replaces_base():
    rules = load_rules(FIXTURES / "override_child.yml")
    aaa_rules = [r for r in rules if r.rule_name == "aaa-model"]
    assert len(aaa_rules) == 1


def test_override_child_severity_wins():
    rules = load_rules(FIXTURES / "override_child.yml")
    aaa_rule = next(r for r in rules if r.rule_name == "aaa-model")
    assert aaa_rule.severity.value == "critical"


def test_override_child_message_wins():
    rules = load_rules(FIXTURES / "override_child.yml")
    aaa_rule = next(r for r in rules if r.rule_name == "aaa-model")
    assert "critical in this environment" in aaa_rule.message
