from c3.loader import _add_child_indent, _normalize_block
from c3.types import Rule


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
