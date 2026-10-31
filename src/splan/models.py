"""Datenmodelle für StarPlan-Antworten."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Semester:
    id: int
    shortname: str
    name: str
    startdate: date | None = None
    enddate: date | None = None


@dataclass(frozen=True)
class Planungsgruppe:
    id: int
    shortname: str
    name: str
    og_id: int = 0
    semester_id: int = 0


@dataclass
class Studiengang:
    id: int
    shortname: str
    name: str
    planungsgruppen: list[Planungsgruppe] = field(default_factory=list)


@dataclass(frozen=True)
class Standort:
    id: int
    shortname: str
    name: str


@dataclass(frozen=True)
class Raum:
    id: int
    shortname: str
    name: str
    standort: Standort


@dataclass(frozen=True)
class Veranstaltung:
    start: str
    ende: str
    titel: str
    import_id: str
    raum: str
    dozent: str
    gruppe: str


@dataclass
class Tag:
    datum: date
    wochentag: str
    veranstaltungen: list[Veranstaltung] = field(default_factory=list)
