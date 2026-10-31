from datetime import date

import pytest

from splan.dates import woche_fuer_optionen
from splan.errors import UsageError


def test_datum_waehlt_montag(monkeypatch) -> None:
    monkeypatch.setenv("SPLAN_HEUTE", "2026-11-02")
    assert woche_fuer_optionen(None, "2026-11-03") == date(2026, 11, 2)


def test_woche_45(monkeypatch) -> None:
    monkeypatch.setenv("SPLAN_HEUTE", "2026-11-02")
    assert woche_fuer_optionen(45, None) == date(2026, 11, 2)


def test_ohne_option_aktuelle_woche(monkeypatch) -> None:
    monkeypatch.setenv("SPLAN_HEUTE", "2026-11-05")
    assert woche_fuer_optionen(None, None) == date(2026, 11, 2)


def test_widerspruch_und_ungueltige_werte(monkeypatch) -> None:
    monkeypatch.setenv("SPLAN_HEUTE", "2026-11-02")
    with pytest.raises(UsageError):
        woche_fuer_optionen(45, "2026-11-03")
    with pytest.raises(UsageError):
        woche_fuer_optionen(None, "03.11.2026")
    with pytest.raises(UsageError):
        woche_fuer_optionen(0, None)
