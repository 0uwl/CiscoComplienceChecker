from c3.conditions import (
    evaluate_condition_block,
)


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