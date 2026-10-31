"""Datums- und Wochenlogik (montags beginnende ISO-Woche)."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from .errors import UsageError

WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


def heute() -> date:
    raw = os.environ.get("SPLAN_HEUTE", "").strip()
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise UsageError(
            f"SPLAN_HEUTE ist kein gültiges Datum: {raw!r}",
            "SPLAN_HEUTE als JJJJ-MM-TT setzen, z. B. 2026-11-02",
        ) from exc


def wochenstart(tag: date) -> date:
    return tag - timedelta(days=tag.weekday())


def wochenende(start: date) -> date:
    return start + timedelta(days=4)


def woche_fuer_optionen(woche: int | None, datum: str | None) -> date:
    if woche is not None and datum is not None:
        raise UsageError(
            "--woche und --datum schließen sich aus",
            "nur eine der beiden Optionen angeben",
        )
    if datum is not None:
        try:
            tag = date.fromisoformat(datum)
        except ValueError as exc:
            raise UsageError(
                f"--datum ist kein gültiges Datum: {datum!r}",
                "--datum als JJJJ-MM-TT angeben, z. B. 2026-11-03",
            ) from exc
        return wochenstart(tag)
    if woche is not None:
        if not 1 <= woche <= 53:
            raise UsageError(
                f"--woche muss zwischen 1 und 53 liegen: {woche}",
                "eine Kalenderwoche angeben, z. B. --woche 45",
            )
        iso_year = heute().isocalendar().year
        try:
            tag = date.fromisocalendar(iso_year, woche, 1)
        except ValueError as exc:
            raise UsageError(
                f"Kalenderwoche {woche} gibt es im Jahr {iso_year} nicht",
                "eine andere Woche mit --woche angeben",
            ) from exc
        return tag
    return wochenstart(heute())


def als_text(tag: date) -> str:
    return tag.strftime("%d.%m.%Y")


def als_iso(tag: date) -> str:
    return tag.isoformat()


def wochentag(tag: date) -> str:
    return WOCHENTAGE[tag.weekday()]


def parse_iso(raw: str) -> date | None:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
