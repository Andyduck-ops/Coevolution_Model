from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_hook_replay_script_passes() -> None:
    result = run_cmd(["bash", ".harness/scripts/hook_replay.sh"])
    assert result.returncode == 0, result.stderr or result.stdout
    assert "[OK] hook replay passed" in result.stdout


def test_ops_full_check_no_blocking_errors() -> None:
    result = run_cmd(["bash", ".harness/scripts/opsctl.sh", "full-check", "--strict"])
    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(result.stdout)
    assert payload["health"]["ok"] is True
    assert payload["spec_audit"]["ok"] is True
