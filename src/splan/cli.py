"""Kommandozeile für splan."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .client import StarPlanClient
from .errors import SplanError, UsageError
from .models import Planungsgruppe, Semester, Studiengang


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
    subparsers = parser.add_subparsers(dest="command", metavar="{suche}")

    suche = subparsers.add_parser(
        "suche",
        help="Studiengang und Planungsgruppen per Name suchen",
        description="Sucht Studiengänge und ihre Planungsgruppen im aktuellen Semester.",
    )
    suche.add_argument("studiengang", metavar="STUDIENGANG", help="Name oder Kürzel")
    suche.set_defaults(func=_cmd_suche)

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
