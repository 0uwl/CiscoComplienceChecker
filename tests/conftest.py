from pathlib import Path

import pytest

from ciscoconfparse2 import CiscoConfParse

from c3.loader import load_rules


BASE_DIR = Path(__file__).parent


def _cfg(name):
    return CiscoConfParse(str(BASE_DIR / "fixtures" / "configs" / name))


@pytest.fixture
def compliant_config():
    return _cfg("compliant.cfg")


@pytest.fixture
def client_access_ports_config():
    return _cfg("client_ports.cfg")


@pytest.fixture
def telnet_config():
    return _cfg("telnet.cfg")


@pytest.fixture
def client_access_compliant_config():
    return _cfg("client_access_compliant.cfg")


@pytest.fixture
def client_no_sticky_config():
    return _cfg("client_no_sticky.cfg")


@pytest.fixture
def access_desc_compliant_config():
    return _cfg("access_desc_compliant.cfg")


@pytest.fixture
def protected_compliant_config():
    return _cfg("protected_compliant.cfg")


@pytest.fixture
def protected_violation_config():
    return _cfg("protected_violation.cfg")


@pytest.fixture
def unused_violation_config():
    return _cfg("unused_violation.cfg")


@pytest.fixture
def unused_skipped_config():
    return _cfg("unused_skipped.cfg")


@pytest.fixture
def rules():
    return load_rules(str(BASE_DIR / "fixtures" / "policies" / "test_policy.yml"))


@pytest.fixture
def interface_rules():
    return load_rules(str(BASE_DIR / "fixtures" / "policies" / "interface_policy.yml"))