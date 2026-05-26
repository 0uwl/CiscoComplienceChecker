from c3.scopes import get_scope_objects


def test_interface_scope(
    compliant_config,
):

    interfaces = get_scope_objects(
        compliant_config,
        "interfaces",
    )

    assert len(interfaces) == 1

    assert interfaces[0].text.startswith(
        "interface"
    )


def test_vty_scope(
    compliant_config,
):

    vty = get_scope_objects(
        compliant_config,
        "vty",
    )

    assert len(vty) == 1