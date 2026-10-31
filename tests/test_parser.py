from pathlib import Path

from splan.parser import parse_timetable

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


def _parse(name: str):
    return parse_timetable((FIXTURES / name).read_text(encoding="utf-8"))


def test_ai1_plan_hat_zwei_tage() -> None:
    tage = _parse("gettt_ai1.html")

    assert [tag.datum.isoformat() for tag in tage] == ["2026-11-02", "2026-11-03"]
    assert tage[0].wochentag == "Montag"
    assert tage[1].wochentag == "Dienstag"
    assert len(tage[0].veranstaltungen) == 2
    assert len(tage[1].veranstaltungen) == 1


def test_ai1_veranstaltung_felder() -> None:
    montag = _parse("gettt_ai1.html")[0]
    erste, zweite = montag.veranstaltungen

    assert erste.start == "08:00"
    assert erste.ende == "09:30"
    assert erste.titel == "Lineare Algebra und Computergrafik"
    assert erste.import_id == "173423"
    assert erste.raum == "A411"
    assert erste.dozent == "Prof. Dr. A. Beispiel"
    assert erste.gruppe == "AI1"

    assert zweite.titel == "Freies Lernen"
    assert zweite.import_id == ""
    assert zweite.raum == "E116"
    assert zweite.dozent == ""


def test_raumplan_hat_gruppe() -> None:
    montag = _parse("gettt_room_a411.html")[0]

    assert len(montag.veranstaltungen) == 2
    assert montag.veranstaltungen[0].gruppe == "AI1"
    assert montag.veranstaltungen[1].titel == "Programmieren 1"
    assert montag.veranstaltungen[1].start == "11:30"


def test_leerer_plan() -> None:
    assert parse_timetable("<div id=\"timetable\"></div>") == []
