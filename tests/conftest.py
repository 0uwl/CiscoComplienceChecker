from pathlib import Path

import pytest

from ciscoconfparse2 import CiscoConfParse

from c3.loader import load_policies


BASE_DIR = Path(__file__).parent


@pytest.fixture
def compliant_config():

    return CiscoConfParse(
        str(
            BASE_DIR
            / "fixtures"
            / "configs"
            / "compliant.cfg"
        )
    )


@pytest.fixture
def telnet_config():

    return CiscoConfParse(
        str(
            BASE_DIR
            / "fixtures"
            / "configs"
            / "telnet.cfg"
        )
    )


@pytest.fixture
def policies():

    return load_policies(
        str(
            BASE_DIR
            / "fixtures"
            / "policies"
            / "test_policy.yml"
        )
    )