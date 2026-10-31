import json
import os
import stat

import pytest

from splan.config import (
    config_path,
    speichere_standardgruppe,
    standardgruppe,
)
from splan.errors import ConfigError


def test_pfad_aus_xdg(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert config_path() == tmp_path / "config" / "splan-cli" / "config.json"


def test_standardgruppe_speichern_und_lesen(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = config_path()
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"anderer": "wert"}), encoding="utf-8")

    gespeichert = speichere_standardgruppe("AI1")

    assert gespeichert == path
    assert standardgruppe() == "AI1"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "anderer": "wert",
        "standard_gruppe": "AI1",
    }
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_keine_standardgruppe(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert standardgruppe() is None


def test_kaputte_konfiguration(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = config_path()
    path.parent.mkdir(parents=True)
    path.write_text("{kaputt", encoding="utf-8")

    with pytest.raises(ConfigError) as excinfo:
        standardgruppe()
    assert excinfo.value.code == 2


def test_nicht_utf8_konfiguration(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = config_path()
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xffkaputt")

    with pytest.raises(ConfigError) as excinfo:
        standardgruppe()
    assert excinfo.value.code == 2
    assert "UTF-8" in excinfo.value.message
    assert "löschen" in excinfo.value.next_step
