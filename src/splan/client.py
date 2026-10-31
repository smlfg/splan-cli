"""HTTP-Client für die öffentlichen StarPlan-Endpunkte."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import date
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from . import __version__
from .dates import heute, parse_iso
from .errors import AccessDeniedError, NotFoundError, SourceError, UsageError
from .models import Planungsgruppe, Raum, Semester, Standort, Studiengang

DEFAULT_BASE_URL = "https://splan.hs-heilbronn.de/splan/"
DEFAULT_TIMEOUT = 15.0


@dataclass
class Response:
    status: int
    content_type: str
    body: bytes
    charset: str | None = None


Fetcher = Callable[[str], Response]


def _urllib_fetch(url: str, timeout: float) -> Response:
    request = Request(
        url,
        headers={
            "User-Agent": f"splan/{__version__}",
            "Accept": "application/json, text/html, text/calendar, */*",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return Response(
                status=int(response.status),
                content_type=response.headers.get_content_type(),
                body=response.read(),
                charset=response.headers.get_content_charset(),
            )
    except HTTPError as exc:
        body = exc.read()
        content_type = ""
        charset = None
        if exc.headers is not None:
            content_type = exc.headers.get_content_type()
            charset = exc.headers.get_content_charset()
        return Response(
            status=int(exc.code),
            content_type=content_type,
            body=body,
            charset=charset,
        )
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        raise SourceError(
            f"StarPlan ist nicht erreichbar: {reason}",
            "Internetverbindung prüfen und den Befehl später erneut ausführen",
        ) from exc


def _validate_base_url(raw: str) -> str:
    value = (raw or "").strip()
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise UsageError(
            f"SPLAN_BASE_URL ist keine gültige HTTP(S)-URL: {raw!r}",
            "SPLAN_BASE_URL als vollständige URL setzen, z. B. https://splan.hs-heilbronn.de/splan/",
        )
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        raise UsageError(
            f"SPLAN_BASE_URL enthält Leerzeichen oder Steuerzeichen: {raw!r}",
            "SPLAN_BASE_URL als vollständige URL ohne Leerzeichen setzen",
        )
    path = parts.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _entries(data: object, quelle: str) -> list[dict]:
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        data = data[0]
    if not isinstance(data, list):
        raise SourceError(
            f"StarPlan liefert für {quelle} unerwartete Daten.",
            "später erneut versuchen; die StarPlan-Schnittstelle kann sich ändern",
        )
    return [item for item in data if isinstance(item, dict)]


def _require_int(item: dict, key: str, quelle: str) -> int:
    value = item.get(key)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SourceError(
            f"StarPlan liefert für {quelle} kein gültiges Feld {key!r}.",
            "später erneut versuchen; die StarPlan-Schnittstelle kann sich ändern",
        ) from exc


def _text(item: dict, key: str) -> str:
    value = item.get(key)
    return "" if value is None else str(value).strip()


def _decode_body(body: bytes, charset: str | None) -> str:
    """Dekodiert StarPlan-Antworten inklusive ISO-8859-1/Windows-1252.

    StarPlan deklariert die JSON-Endpunkte als ``ISO-8859-1``, liefert aber
    Umlaute in Einzelbytes (z. B. 0xfc für „ü“). Zuerst wird der deklarierte
    Zeichensatz versucht, danach UTF-8 und als letzter Ausweg Windows-1252.
    """
    if charset:
        try:
            return body.decode(charset)
        except (LookupError, UnicodeDecodeError):
            pass
    try:
        return body.decode("utf-8-sig")
    except UnicodeDecodeError:
        return body.decode("cp1252", "replace")


class StarPlanClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        fetcher: Fetcher | None = None,
        today: date | None = None,
    ) -> None:
        raw = base_url
        if raw is None:
            raw = os.environ.get("SPLAN_BASE_URL") or DEFAULT_BASE_URL
        self.base_url = _validate_base_url(raw)
        self.timeout = timeout
        self.fetcher = fetcher or (lambda url: _urllib_fetch(url, timeout))
        self.today = today or heute()
        self._semester: Semester | None = None

    def _url(self, endpoint: str, params: dict[str, object] | None = None) -> str:
        url = self.base_url + endpoint
        if params:
            url += "?" + urlencode(params)
        return url

    def _get(self, url: str) -> Response:
        response = self.fetcher(url)
        if response.status in {401, 403}:
            raise AccessDeniedError(
                f"StarPlan verweigert den Zugriff (HTTP {response.status}).",
                "später erneut versuchen; für splan ist kein Login vorgesehen",
            )
        if not 200 <= response.status < 300:
            raise SourceError(
                f"StarPlan antwortet mit HTTP {response.status}.",
                "später erneut versuchen oder SPLAN_BASE_URL prüfen",
            )
        return response

    def _get_json(self, params: dict[str, object], quelle: str) -> object:
        response = self._get(self._url("json", params))
        try:
            return json.loads(_decode_body(response.body, response.charset))
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"StarPlan liefert für {quelle} kein gültiges JSON.",
                "später erneut versuchen; die StarPlan-Schnittstelle kann sich ändern",
            ) from exc

    def _get_text(self, url: str, quelle: str) -> str:
        response = self._get(url)
        return _decode_body(response.body, response.charset)

    def semesters(self) -> list[Semester]:
        data = self._get_json({"m": "getpus"}, "getpus")
        result: list[Semester] = []
        for item in _entries(data, "getpus"):
            result.append(
                Semester(
                    id=_require_int(item, "id", "getpus"),
                    shortname=_text(item, "shortname"),
                    name=_text(item, "name"),
                    startdate=parse_iso(_text(item, "startdate")),
                    enddate=parse_iso(_text(item, "enddate")),
                )
            )
        return result

    def current_semester(self) -> Semester:
        if self._semester is not None:
            return self._semester
        semesters = self.semesters()
        if not semesters:
            raise SourceError(
                "StarPlan liefert kein Semester.",
                "später erneut versuchen oder SPLAN_BASE_URL prüfen",
            )
        today = self.today
        aktiv = [
            item
            for item in semesters
            if item.startdate is not None
            and item.enddate is not None
            and item.startdate <= today <= item.enddate
        ]
        if aktiv:
            self._semester = max(aktiv, key=lambda item: item.startdate or date.min)
            return self._semester
        mit_start = [item for item in semesters if item.startdate is not None]
        vergangen = [item for item in mit_start if item.startdate <= today]  # type: ignore[operator]
        if vergangen:
            self._semester = max(vergangen, key=lambda item: item.startdate or date.min)
        elif mit_start:
            self._semester = min(mit_start, key=lambda item: item.startdate or date.max)
        else:
            self._semester = semesters[0]
        return self._semester

    def studiengaenge(self, pu: int) -> list[Studiengang]:
        data = self._get_json({"m": "getogs", "pu": pu}, "getogs")
        result: list[Studiengang] = []
        for item in _entries(data, "getogs"):
            result.append(
                Studiengang(
                    id=_require_int(item, "id", "getogs"),
                    shortname=_text(item, "shortname"),
                    name=_text(item, "name"),
                )
            )
        return result

    def planungsgruppen(self, pu: int, og: int) -> list[Planungsgruppe]:
        data = self._get_json(
            {"m": "getPgsExt", "pu": pu, "og": og}, "getPgsExt"
        )
        result: list[Planungsgruppe] = []
        for item in _entries(data, "getPgsExt"):
            result.append(
                Planungsgruppe(
                    id=_require_int(item, "id", "getPgsExt"),
                    shortname=_text(item, "shortname"),
                    name=_text(item, "name"),
                    og_id=og,
                    semester_id=pu,
                )
            )
        return result

    def standorte(self) -> list[Standort]:
        data = self._get_json({"m": "getlocs"}, "getlocs")
        result: list[Standort] = []
        for item in _entries(data, "getlocs"):
            result.append(
                Standort(
                    id=_require_int(item, "id", "getlocs"),
                    shortname=_text(item, "shortname"),
                    name=_text(item, "name"),
                )
            )
        return result

    def raeume(self, loc: int) -> list[dict]:
        data = self._get_json({"m": "getros", "loc": loc}, "getros")
        return _entries(data, "getros")

    def alle_raeume(self) -> list[Raum]:
        result: list[Raum] = []
        for standort in self.standorte():
            for item in self.raeume(standort.id):
                result.append(
                    Raum(
                        id=_require_int(item, "id", "getros"),
                        shortname=_text(item, "shortname"),
                        name=_text(item, "name"),
                        standort=standort,
                    )
                )
        return result

    def finde_raum(self, begriff: str) -> Raum:
        needle = begriff.casefold().strip()
        raeume = self.alle_raeume()
        exakt = [item for item in raeume if needle == item.shortname.casefold()]
        kandidaten = exakt or [
            item
            for item in raeume
            if needle in item.shortname.casefold() or needle in item.name.casefold()
        ]
        if not kandidaten:
            raise NotFoundError(
                f"Raum {begriff!r} nicht gefunden.",
                f"einen anderen Raumnamen verwenden, z. B. splan raum {begriff}",
            )
        if len(kandidaten) > 1:
            namen = ", ".join(
                f"{item.shortname} ({item.standort.shortname})"
                for item in kandidaten[:8]
            )
            raise NotFoundError(
                f"Raum {begriff!r} ist nicht eindeutig: {namen}",
                "den Raumnamen präzisieren, z. B. splan raum A411",
            )
        return kandidaten[0]

    def alle_planungsgruppen(self, semester: Semester) -> list[Planungsgruppe]:
        result: list[Planungsgruppe] = []
        seen: set[int] = set()
        for studiengang in self.studiengaenge(semester.id):
            for gruppe in self.planungsgruppen(semester.id, studiengang.id):
                if gruppe.id in seen:
                    continue
                seen.add(gruppe.id)
                result.append(
                    replace(
                        gruppe,
                        og_id=studiengang.id,
                        semester_id=semester.id,
                    )
                )
        return result

    def suche_studiengaenge(self, begriff: str) -> tuple[Semester, list[Studiengang]]:
        semester = self.current_semester()
        needle = begriff.casefold().strip()
        treffer: list[Studiengang] = []
        for studiengang in self.studiengaenge(semester.id):
            if (
                needle in studiengang.name.casefold()
                or needle in studiengang.shortname.casefold()
            ):
                studiengang.planungsgruppen = self.planungsgruppen(
                    semester.id, studiengang.id
                )
                treffer.append(studiengang)
        if not treffer:
            raise NotFoundError(
                f"Kein Studiengang gefunden für {begriff!r}.",
                "einen anderen Suchbegriff verwenden, z. B. splan suche Informatik",
            )
        return semester, treffer

    def finde_gruppe(self, begriff: str) -> tuple[Semester, Planungsgruppe]:
        semester = self.current_semester()
        needle = begriff.casefold().strip()
        gruppen = self.alle_planungsgruppen(semester)
        exakt = [
            item
            for item in gruppen
            if needle == item.shortname.casefold() or needle == item.name.casefold()
        ]
        kandidaten = exakt or [
            item
            for item in gruppen
            if needle in item.shortname.casefold() or needle in item.name.casefold()
        ]
        if not kandidaten:
            raise NotFoundError(
                f"Gruppe {begriff!r} nicht gefunden.",
                f"splan suche {begriff} ausführen",
            )
        if len(kandidaten) > 1:
            namen = ", ".join(
                f"{item.shortname} ({item.name})" for item in kandidaten[:8]
            )
            raise NotFoundError(
                f"Gruppe {begriff!r} ist mehrdeutig: {namen}",
                f"den Gruppennamen präzisieren oder splan suche {begriff} ausführen",
            )
        return semester, kandidaten[0]

    def timetable_pg(
        self, semester: Semester, gruppe: Planungsgruppe, week_start: date
    ) -> str:
        params = {
            "m": "getTT",
            "sel": "pg",
            "pu": semester.id,
            "og": gruppe.og_id,
            "pg": gruppe.shortname,
            "sd": "true",
            "dfc": week_start.isoformat(),
        }
        return self._get_text(self._url("json", params), "getTT")

    def timetable_room(
        self, semester: Semester, raum: Raum, week_start: date
    ) -> str:
        params = {
            "m": "getTT",
            "sel": "ro",
            "pu": semester.id,
            "ro": raum.id,
            "sd": "true",
            "dfc": week_start.isoformat(),
        }
        return self._get_text(self._url("json", params), "getTT")

    def ical_pg(self, semester: Semester, gruppe: Planungsgruppe) -> bytes:
        params = {
            "lan": "de",
            "puid": semester.id,
            "type": "pg",
            "pgid": gruppe.id,
        }
        return self._get(self._url("ical", params)).body
