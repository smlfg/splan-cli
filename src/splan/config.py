"""Konfiguration für die Standardgruppe."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ConfigError

SCHLUESSEL = "standard_gruppe"


def config_path() -> Path:
    raw = os.environ.get("XDG_CONFIG_HOME", "").strip()
    basis = Path(raw).expanduser() if raw else Path.home() / ".config"
    return basis / "splan-cli" / "config.json"


def _lesen(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except UnicodeDecodeError as exc:
        raise ConfigError(
            f"Konfiguration {str(path)!r} ist nicht gültig UTF-8-kodiert.",
            "die Datei korrigieren oder löschen, danach splan standard GRUPPE ausführen",
        ) from exc
    except OSError as exc:
        raise ConfigError(
            f"Konfiguration {str(path)!r} ist nicht lesbar: {exc.strerror or exc}",
            "Schreibrechte prüfen oder XDG_CONFIG_HOME auf ein beschreibbares Verzeichnis setzen",
        ) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Konfiguration {str(path)!r} ist kein gültiges JSON.",
            "die Datei korrigieren oder löschen, danach splan standard GRUPPE ausführen",
        ) from exc
    if not isinstance(data, dict):
        raise ConfigError(
            f"Konfiguration {str(path)!r} enthält kein JSON-Objekt.",
            "die Datei korrigieren oder löschen, danach splan standard GRUPPE ausführen",
        )
    return data


def standardgruppe() -> str | None:
    data = _lesen(config_path())
    value = data.get(SCHLUESSEL)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(
            f"Standardgruppe in {str(config_path())!r} ist ungültig.",
            "splan standard GRUPPE ausführen oder den Eintrag korrigieren",
        )
    return value.strip()


def speichere_standardgruppe(gruppe: str) -> Path:
    path = config_path()
    data = _lesen(path)
    data[SCHLUESSEL] = gruppe
    tmp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise ConfigError(
            f"Konfiguration {str(path)!r} konnte nicht geschrieben werden: {exc.strerror or exc}",
            "Schreibrechte prüfen oder XDG_CONFIG_HOME auf ein beschreibbares Verzeichnis setzen",
        ) from exc
    return path
