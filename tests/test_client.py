import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from splan.client import Response, StarPlanClient
from splan.errors import AccessDeniedError, NotFoundError, SourceError, UsageError

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


class FixtureFetcher:
    """Liest Antworten aus tests/fixtures/ux, ohne das Netz zu berühren."""

    def __init__(self, routes: list[tuple[str, str, str]]) -> None:
        self.routes = routes
        self.urls: list[str] = []

    def __call__(self, url: str) -> Response:
        self.urls.append(url)
        query = urlsplit(url).query
        for needle, name, content_type in self.routes:
            if needle in query:
                body = (FIXTURES / name).read_bytes()
                return Response(200, content_type, body)
        return Response(404, "text/plain", b"not found")


ROUTES = [
    ("m=getpus", "getpus.json", "application/json"),
    ("m=getogs", "getogs.json", "application/json"),
    ("m=getPgsExt", "getpgs_ai.json", "application/json"),
    ("sel=ro", "gettt_room_a411.html", "text/html"),
    ("m=getTT", "gettt_ai1.html", "text/html"),
    ("m=getlocs", "getlocs.json", "application/json"),
    ("loc=2", "getros_loc2.json", "application/json"),
    ("m=getros", "getros_empty.json", "application/json"),
    ("lan=de", "ical_ai1.ics", "text/calendar"),
]


def _client(**kwargs) -> StarPlanClient:
    fetcher = FixtureFetcher(ROUTES)
    return StarPlanClient(
        "http://127.0.0.1:9/splan/",
        fetcher=fetcher,
        today=date(2026, 11, 2),
        **kwargs,
    )


def test_semester_und_studiengaenge() -> None:
    client = _client()

    semester = client.current_semester()
    assert semester.id == 48
    assert semester.name == "Wintersemester 2026/2027"
    assert [item.shortname for item in client.studiengaenge(48)] == ["AI", "AKI", "MIB"]


def test_suche_findet_gruppen() -> None:
    client = _client()

    semester, treffer = client.suche_studiengaenge("Angewandte Informatik")

    assert semester.id == 48
    assert len(treffer) == 1
    assert treffer[0].shortname == "AI"
    assert [pg.shortname for pg in treffer[0].planungsgruppen] == ["AI1", "AI2", "AI3"]


def test_gruppe_exakt_und_name() -> None:
    client = _client()

    _, gruppe = client.finde_gruppe("AI1")
    assert gruppe.id == 30350
    assert gruppe.og_id == 725

    _, gruppe = client.finde_gruppe("AI 1. Semester")
    assert gruppe.shortname == "AI1"


def test_unbekannte_gruppe() -> None:
    client = _client()

    with pytest.raises(NotFoundError) as excinfo:
        client.finde_gruppe("AI9")

    assert excinfo.value.code == 1
    assert "splan suche" in excinfo.value.next_step


def test_timetable_und_ical() -> None:
    client = _client()
    semester, gruppe = client.finde_gruppe("AI1")

    html = client.timetable_pg(semester, gruppe, date(2026, 11, 2))
    assert "Lineare Algebra und Computergrafik" in html

    ical = client.ical_pg(semester, gruppe)
    assert b"BEGIN:VCALENDAR" in ical
    assert b"BEGIN:VEVENT" in ical


def test_raumliste() -> None:
    client = _client()
    raeume = client.raeume(2)
    assert any(item.get("shortname") == "A411" for item in raeume)


def test_raum_exakt_und_teilstring() -> None:
    client = _client()

    raum = client.finde_raum("A411")
    assert raum.id == 71
    assert raum.standort.shortname == "TechCampus HN"

    raum = client.finde_raum("SSI")
    assert raum.shortname == "A208"


def test_unbekannter_raum() -> None:
    client = _client()

    with pytest.raises(NotFoundError) as excinfo:
        client.finde_raum("Z999")

    assert excinfo.value.code == 1
    assert "splan raum" in excinfo.value.next_step


def test_fehlercodes() -> None:
    def status(code: int):
        return lambda url: Response(code, "text/plain", b"")

    with pytest.raises(SourceError) as excinfo:
        StarPlanClient("http://127.0.0.1:9/", fetcher=status(500)).semesters()
    assert excinfo.value.code == 3

    with pytest.raises(AccessDeniedError) as excinfo:
        StarPlanClient("http://127.0.0.1:9/", fetcher=status(403)).semesters()
    assert excinfo.value.code == 4


def test_ungueltige_basis_url() -> None:
    with pytest.raises(UsageError) as excinfo:
        StarPlanClient("keine-url")
    assert excinfo.value.code == 2


def test_kaputtes_json() -> None:
    client = StarPlanClient(
        "http://127.0.0.1:9/",
        fetcher=lambda url: Response(200, "application/json", b"{kaputt"),
    )
    with pytest.raises(SourceError) as excinfo:
        client.semesters()
    assert excinfo.value.code == 3


def test_iso_8859_1_json_mit_umlauten() -> None:
    body = json.dumps(
        [
            [
                {
                    "id": 1379,
                    "shortname": "AKI",
                    "name": "Angewandte Künstliche Intelligenz",
                }
            ]
        ],
        ensure_ascii=False,
    ).encode("cp1252")
    client = StarPlanClient(
        "http://127.0.0.1:9/",
        fetcher=lambda url: Response(
            200, "application/json", body, charset="ISO-8859-1"
        ),
    )

    treffer = client.studiengaenge(48)

    assert treffer[0].name == "Angewandte Künstliche Intelligenz"


def test_iso_8859_1_ohne_charset_erkannt() -> None:
    body = json.dumps(
        [[{"id": 1379, "shortname": "AKI", "name": "Künstliche Intelligenz"}]],
        ensure_ascii=False,
    ).encode("cp1252")
    client = StarPlanClient(
        "http://127.0.0.1:9/",
        fetcher=lambda url: Response(200, "application/json", body),
    )

    treffer = client.studiengaenge(48)

    assert treffer[0].name == "Künstliche Intelligenz"
