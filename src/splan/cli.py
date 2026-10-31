"""Kommandozeile für splan."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta

from . import __version__
from .client import StarPlanClient
from .dates import (
    als_text,
    woche_fuer_optionen,
    wochenende,
    wochenstart,
    wochentag,
)
from .errors import NotFoundError, SplanError, UsageError
from .models import (
    Planungsgruppe,
    Raum,
    Semester,
    Studiengang,
    Tag,
    Veranstaltung,
)
from .parser import parse_timetable


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message, "splan --help ausführen")


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="splan",
        description=(
            "Stundenpläne der Hochschule Heilbronn aus StarPlan im Terminal. "
            "Nur öffentliche Lese-Anfragen, kein Login."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="genau ein JSON-Objekt auf stdout ausgeben",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"splan {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="{suche,plan,heute,raum}")

    suche = subparsers.add_parser(
        "suche",
        help="Studiengang und Planungsgruppen per Name suchen",
        description="Sucht Studiengänge und ihre Planungsgruppen im aktuellen Semester.",
    )
    suche.add_argument("studiengang", metavar="STUDIENGANG", help="Name oder Kürzel")
    suche.set_defaults(func=_cmd_suche)

    plan = subparsers.add_parser(
        "plan",
        help="Wochenplan einer Planungsgruppe anzeigen",
        description="Zeigt den Plan einer Planungsgruppe für eine Woche.",
    )
    plan.add_argument("gruppe", metavar="GRUPPE", help="Kürzel oder Name der Gruppe")
    plan.add_argument(
        "--woche", type=int, metavar="KW", help="Kalenderwoche nach ISO 8601"
    )
    plan.add_argument(
        "--datum", metavar="JJJJ-MM-TT", help="ein Tag in der gewünschten Woche"
    )
    plan.set_defaults(func=_cmd_plan)

    heute = subparsers.add_parser(
        "heute",
        help="heutigen Stundenplan anzeigen",
        description="Zeigt nur den heutigen Tag; ohne Gruppe gilt die Standardgruppe.",
    )
    heute.add_argument(
        "gruppe", nargs="?", metavar="GRUPPE", help="Kürzel oder Name der Gruppe"
    )
    heute.set_defaults(func=_cmd_heute)

    raum = subparsers.add_parser(
        "raum",
        help="Belegung eines Raums anzeigen",
        description=(
            "Sucht einen Raum über alle Standorte und zeigt seine Belegung "
            "für die aktuelle Woche."
        ),
    )
    raum.add_argument("raumname", metavar="RAUMNAME", help="Kürzel oder Name des Raums")
    raum.set_defaults(func=_cmd_raum)

    return parser


def _semester_json(semester: Semester) -> dict:
    return {
        "id": semester.id,
        "shortname": semester.shortname,
        "name": semester.name,
    }


def _gruppe_json(gruppe: Planungsgruppe) -> dict:
    return {
        "id": gruppe.id,
        "shortname": gruppe.shortname,
        "name": gruppe.name,
    }


def _studiengang_json(studiengang: Studiengang) -> dict:
    return {
        "id": studiengang.id,
        "shortname": studiengang.shortname,
        "name": studiengang.name,
        "planungsgruppen": [
            _gruppe_json(gruppe) for gruppe in studiengang.planungsgruppen
        ],
    }


def _emit_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _veranstaltung_json(item: Veranstaltung) -> dict:
    return {
        "start": item.start,
        "ende": item.ende,
        "titel": item.titel,
        "import_id": item.import_id,
        "raum": item.raum,
        "dozent": item.dozent,
        "gruppe": item.gruppe,
    }


def _tag_json(tag: Tag) -> dict:
    return {
        "datum": tag.datum.isoformat(),
        "wochentag": tag.wochentag,
        "veranstaltungen": [
            _veranstaltung_json(item) for item in tag.veranstaltungen
        ],
    }


def _print_veranstaltung(item: Veranstaltung, mit_gruppe: bool = False) -> None:
    import_id = f" ({item.import_id})" if item.import_id else ""
    zeile = f"{item.start}-{item.ende}  {item.titel}{import_id}"
    if mit_gruppe:
        if item.gruppe:
            zeile += f" · {item.gruppe}"
        print(zeile)
        return
    print(zeile)
    raum = f"Raum {item.raum}" if item.raum else ""
    if raum and item.dozent:
        print(f"{raum} · {item.dozent}")
    elif raum:
        print(raum)
    elif item.dozent:
        print(item.dozent)


def _woche_pruefen(semester: Semester, week_start) -> None:
    week_end = wochenende(week_start)
    if semester.startdate is not None and week_end < semester.startdate:
        raise NotFoundError(
            f"Die Woche {als_text(week_start)} bis {als_text(week_end)} liegt "
            f"vor dem Semester {semester.name}.",
            "--woche oder --datum innerhalb des Semesters wählen",
        )
    if semester.enddate is not None and week_start > semester.enddate:
        raise NotFoundError(
            f"Die Woche {als_text(week_start)} bis {als_text(week_end)} liegt "
            f"nach dem Semester {semester.name}.",
            "--woche oder --datum innerhalb des Semesters wählen",
        )


def _cmd_suche(args: argparse.Namespace, client: StarPlanClient, json_mode: bool) -> int:
    semester, treffer = client.suche_studiengaenge(args.studiengang)
    if json_mode:
        _emit_json(
            {
                "ok": True,
                "semester": _semester_json(semester),
                "treffer": [_studiengang_json(item) for item in treffer],
            }
        )
        return 0

    print(f"Semester: {semester.name}")
    for studiengang in treffer:
        print(f"{studiengang.name} ({studiengang.shortname})")
        for gruppe in studiengang.planungsgruppen:
            print(f"{gruppe.shortname} – {gruppe.name}")
    return 0


def _cmd_plan(args: argparse.Namespace, client: StarPlanClient, json_mode: bool) -> int:
    week_start = woche_fuer_optionen(args.woche, args.datum)
    semester, gruppe = client.finde_gruppe(args.gruppe)
    _woche_pruefen(semester, week_start)
    html = client.timetable_pg(semester, gruppe, week_start)
    fallback = [week_start + timedelta(days=i) for i in range(5)]
    tage = parse_timetable(html, fallback)
    if json_mode:
        _emit_json(
            {
                "ok": True,
                "gruppe": _gruppe_json(gruppe),
                "semester": {"id": semester.id, "name": semester.name},
                "woche": {
                    "von": week_start.isoformat(),
                    "bis": wochenende(week_start).isoformat(),
                },
                "tage": [_tag_json(tag) for tag in tage],
            }
        )
        return 0

    print(
        f"Plan {gruppe.shortname} – Woche {als_text(week_start)} bis "
        f"{als_text(wochenende(week_start))}"
    )
    for tag in tage:
        print(f"{tag.wochentag}, {als_text(tag.datum)}")
        for item in tag.veranstaltungen:
            _print_veranstaltung(item)
    return 0


def _cmd_heute(args: argparse.Namespace, client: StarPlanClient, json_mode: bool) -> int:
    if not args.gruppe:
        raise NotFoundError(
            "Keine Standardgruppe gespeichert.",
            "splan standard GRUPPE ausführen oder eine Gruppe angeben",
        )
    today = client.today
    week_start = wochenstart(today)
    semester, gruppe = client.finde_gruppe(args.gruppe)
    _woche_pruefen(semester, week_start)
    html = client.timetable_pg(semester, gruppe, week_start)
    fallback = [week_start + timedelta(days=i) for i in range(5)]
    tage = parse_timetable(html, fallback)
    tag = next((item for item in tage if item.datum == today), None)
    if tag is None:
        tag = Tag(datum=today, wochentag=wochentag(today))
    if json_mode:
        _emit_json(
            {
                "ok": True,
                "heute": today.isoformat(),
                "gruppe": _gruppe_json(gruppe),
                "semester": {"id": semester.id, "name": semester.name},
                "woche": {
                    "von": week_start.isoformat(),
                    "bis": wochenende(week_start).isoformat(),
                },
                "tage": [_tag_json(tag)],
            }
        )
        return 0

    print(f"Heute, {tag.wochentag} {als_text(tag.datum)} – {gruppe.shortname}")
    if not tag.veranstaltungen:
        print("Keine Veranstaltungen.")
        return 0
    for item in tag.veranstaltungen:
        _print_veranstaltung(item)
    return 0


def _raum_json(raum: Raum) -> dict:
    return {
        "id": raum.id,
        "shortname": raum.shortname,
        "name": raum.name,
        "standort": {
            "id": raum.standort.id,
            "shortname": raum.standort.shortname,
            "name": raum.standort.name,
        },
    }


def _cmd_raum(args: argparse.Namespace, client: StarPlanClient, json_mode: bool) -> int:
    week_start = woche_fuer_optionen(None, None)
    raum = client.finde_raum(args.raumname)
    semester = client.current_semester()
    _woche_pruefen(semester, week_start)
    html = client.timetable_room(semester, raum, week_start)
    fallback = [week_start + timedelta(days=i) for i in range(5)]
    tage = parse_timetable(html, fallback)
    if json_mode:
        _emit_json(
            {
                "ok": True,
                "raum": _raum_json(raum),
                "woche": {
                    "von": week_start.isoformat(),
                    "bis": wochenende(week_start).isoformat(),
                },
                "tage": [_tag_json(tag) for tag in tage],
            }
        )
        return 0

    print(f"Raum {raum.shortname} – {raum.standort.shortname}")
    for tag in tage:
        print(f"{tag.wochentag}, {als_text(tag.datum)}")
        for item in tag.veranstaltungen:
            _print_veranstaltung(item, mit_gruppe=True)
    return 0


def _report_error(error: SplanError, json_mode: bool) -> int:
    next_step = error.next_step or "splan --help ausführen"
    if json_mode:
        _emit_json(
            {
                "ok": False,
                "fehler": error.message,
                "naechster_schritt": next_step,
            }
        )
    else:
        print(f"Fehler: {error.message}", file=sys.stderr)
        print(f"Nächster Schritt: {next_step}", file=sys.stderr)
    return error.code


def _configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def main(argv: list[str] | None = None) -> int:
    _configure_streams()
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_requested = "--json" in arguments
    parser = _build_parser()
    try:
        args = parser.parse_args(arguments)
        json_mode = bool(getattr(args, "json", False)) or not sys.stdout.isatty()
        if getattr(args, "command", None) is None:
            if json_requested or not sys.stdout.isatty():
                raise UsageError(
                    "Unterkommando fehlt.",
                    "splan --help ausführen und ein Unterkommando wählen",
                )
            parser.print_help(sys.stderr)
            print(
                "Nächster Schritt: ein Unterkommando wählen, z. B. splan suche Informatik",
                file=sys.stderr,
            )
            return 2
        client = StarPlanClient()
        return int(args.func(args, client, json_mode))
    except SplanError as error:
        return _report_error(
            error, json_requested or not sys.stdout.isatty()
        )
    except (KeyboardInterrupt, EOFError):
        return _report_error(
            SplanError("Abgebrochen.", "splan --help ausführen"),
            json_requested or not sys.stdout.isatty(),
        )
    except BrokenPipeError:
        return 0
