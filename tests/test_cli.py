import io
import json
import os
import subprocess
import sys
from pathlib import Path

from splan.cli import main

REPO = Path(__file__).resolve().parents[1]
ENV = {
    **os.environ,
    "PYTHONPATH": str(REPO / "src"),
    "PYTHONDONTWRITEBYTECODE": "1",
}


def _run(*args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        [sys.executable, "-m", "splan", *args],
        capture_output=True,
        text=True,
        env=(env or ENV),
        check=False,
    )


def test_version_und_help_exit_null() -> None:
    version = _run("--version")
    assert version.returncode == 0
    assert version.stdout.startswith("splan ")

    help_result = _run("--help")
    assert help_result.returncode == 0
    for name in ("suche", "plan", "heute", "raum", "ics", "standard"):
        assert name in help_result.stdout

    for name in ("suche", "plan", "heute", "raum", "ics", "standard"):
        sub = _run(name, "--help")
        assert sub.returncode == 0, sub.stderr


def test_ohne_unterkommando_json_fehler() -> None:
    result = _run("--json")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Unterkommando" in payload["fehler"]
    assert "Traceback" not in result.stderr


def test_unbekanntes_unterkommando_json_fehler() -> None:
    result = _run("--json", "quatsch")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "invalid choice" in payload["fehler"]


def test_ungueltige_basis_url_ohne_traceback() -> None:
    env = {**ENV, "SPLAN_BASE_URL": "http://bei spiel/"}
    result = _run("--json", "suche", "AI", env=env)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "SPLAN_BASE_URL" in payload["fehler"]
    assert "Traceback" not in result.stderr


def test_ungueltiges_testdatum_ohne_traceback() -> None:
    env = {**ENV, "SPLAN_HEUTE": "32.13.2026"}
    result = _run("--json", "heute", "AI1", env=env)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "SPLAN_HEUTE" in payload["fehler"]
    assert "Traceback" not in result.stderr


def test_kaputte_konfiguration_ohne_traceback(tmp_path, monkeypatch) -> None:
    config_home = tmp_path / "config"
    path = config_home / "splan-cli" / "config.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xffkaputt")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    stdout = Terminal()
    stderr = Terminal()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    code = main(["heute"])

    assert code == 2
    assert "UTF-8" in stderr.getvalue()
    assert "Nächster Schritt" in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()
    assert "Traceback" not in stdout.getvalue()


def test_kaputte_konfiguration_json_ohne_traceback(tmp_path) -> None:
    config_home = tmp_path / "config"
    path = config_home / "splan-cli" / "config.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xffkaputt")
    env = {**ENV, "XDG_CONFIG_HOME": str(config_home)}

    result = _run("--json", "heute", env=env)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "UTF-8" in payload["fehler"]
    assert "löschen" in payload["naechster_schritt"]
    assert result.stderr == ""
