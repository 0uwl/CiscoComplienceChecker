from c3.evaluator import (
    evaluate_rule,
)


def test_compliant_rule(
    compliant_config,
    policies,
):

    aaa_rule = next(
        r
        for r in policies
        if r.rule_name == "aaa-model"
    )

    violations = evaluate_rule(
        compliant_config,
        aaa_rule,
    )

    assert violations == []


def test_telnet_violation(
    telnet_config,
    policies,
):

    telnet_rule = next(
        r
        for r in policies
        if r.rule_name == "no-telnet"
    )

    violations = evaluate_rule(
        telnet_config,
        telnet_rule,
    )

    assert len(violations) == 1

    violation = violations[0]

    assert violation.rule == "no-telnet"

    assert (
        violation.severity.value
        == "critical"
    )