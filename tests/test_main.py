import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from c3.main import evaluate_config, main, scan_directory, _worst_exit_code


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


# --- Directory scan ---


def _make_cfg(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return p


def test_scan_directory_returns_one_result_per_cfg(tmp_path):
    clean = (BASE_DIR / "fixtures" / "configs" / "clean.cfg").read_text()
    warnings = (BASE_DIR / "fixtures" / "configs" / "warnings_only.cfg").read_text()
    _make_cfg(tmp_path, "a.cfg", clean)
    _make_cfg(tmp_path, "b.cfg", warnings)
    _make_cfg(tmp_path, "not_a_config.txt", "ignored")

    results = scan_directory(tmp_path, POLICY)

    assert len(results) == 2
    devices = {r["device"] for r in results}
    assert devices == {"a", "b"}


def test_scan_directory_empty_dir(tmp_path):
    results = scan_directory(tmp_path, POLICY)
    assert results == []


def test_worst_exit_code_all_ok():
    assert _worst_exit_code([{"status": "ok"}, {"status": "ok"}]) == 0


def test_worst_exit_code_any_warning():
    assert _worst_exit_code([{"status": "ok"}, {"status": "warning"}]) == 1


def test_worst_exit_code_any_critical():
    assert _worst_exit_code([{"status": "warning"}, {"status": "critical"}]) == 2


def test_main_dir_outputs_json_array(tmp_path, capsys):
    clean = (BASE_DIR / "fixtures" / "configs" / "clean.cfg").read_text()
    _make_cfg(tmp_path, "device.cfg", clean)

    args = ["c3", "--dir", str(tmp_path), str(POLICY)]
    with patch("sys.argv", args), pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert isinstance(output, list)
    assert output[0]["device"] == "device"
    assert output[0]["status"] == "ok"


def test_main_dir_exit_code_reflects_worst(tmp_path):
    telnet = (BASE_DIR / "fixtures" / "configs" / "telnet.cfg").read_text()
    clean = (BASE_DIR / "fixtures" / "configs" / "clean.cfg").read_text()
    _make_cfg(tmp_path, "bad.cfg", telnet)
    _make_cfg(tmp_path, "good.cfg", clean)

    args = ["c3", "--dir", str(tmp_path), str(POLICY)]
    with patch("sys.argv", args), pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
