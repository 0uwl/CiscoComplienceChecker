import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from c3.main import evaluate_config, main


BASE_DIR = Path(__file__).parent
POLICY = BASE_DIR / "fixtures" / "policies" / "test_policy.yml"


def test_score_is_100_when_fully_compliant():
    result = evaluate_config(
        BASE_DIR / "fixtures" / "configs" / "clean.cfg",
        POLICY,
    )
    assert result["score"] == 100
    assert result["violations"] == []
    assert result["status"] == "ok"


def test_score_deducts_per_severity():
    # telnet.cfg: 3 warnings (-30) + 1 critical (-50) = 20
    result = evaluate_config(
        BASE_DIR / "fixtures" / "configs" / "telnet.cfg",
        POLICY,
    )
    assert result["score"] == 20


def test_score_clamped_to_zero():
    # overloaded.cfg: 3 criticals (-150) + 3 warnings (-30) = -80, clamped to 0
    result = evaluate_config(
        BASE_DIR / "fixtures" / "configs" / "overloaded.cfg",
        POLICY,
    )
    assert result["score"] == 0


def _run_main(cfg_name):
    args = ["c3", str(BASE_DIR / "fixtures" / "configs" / cfg_name), str(POLICY)]
    with patch("sys.argv", args), pytest.raises(SystemExit) as exc:
        main()
    return exc.value.code


def test_exit_code_0_when_compliant():
    assert _run_main("clean.cfg") == 0


def test_exit_code_1_when_warnings_only():
    assert _run_main("warnings_only.cfg") == 1


def test_exit_code_2_when_critical():
    assert _run_main("telnet.cfg") == 2
