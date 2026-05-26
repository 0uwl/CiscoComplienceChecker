from c3.types import Rule


def test_policy_loader(rules):

    assert len(rules) == 9

    rule = rules[0]

    assert isinstance(rule, Rule)

    assert rule.rule_name == "aaa-model"

    assert rule.scope == "global"

    assert rule.severity.value == "warning"