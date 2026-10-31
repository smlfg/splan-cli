"""Akzeptanztests aus docs/UX.md gegen den lokalen Fake-Server.

Je UX-Sitzung gibt es mindestens einen Test. Das Tool läuft als echter
Subprozess in einer PTY, damit es die menschenlesbare Textausgabe erzeugt
(stdout ist ein Terminal). Die Netzwerk-Sandbox aus tests/harness erlaubt
nur Verbindungen zu localhost.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "tests" / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from fake_server import FakeServer  # noqa: E402
from ux_session import PtySession, build_env, strip_ansi  # noqa: E402
from ux_spec import parse  # noqa: E402

SPEC = parse(REPO / "docs" / "UX.md")
HEUTE = str((SPEC.meta or {}).get("env", {}).get("SPLAN_HEUTE", "2026-11-02"))
SCRATCH = REPO / "scratch" / "tmp" / "acceptance"


def _temp_home(prefix: str) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{prefix}-", dir=SCRATCH))


@contextmanager
def _fake_server(prefix: str):
    home = _temp_home(prefix)
    try:
        with FakeServer(SPEC, REPO) as server:
            bin_dir = home / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            env = build_env(SPEC, server, home, bin_dir, REPO)
            env["SPLAN_HEUTE"] = HEUTE
            env["PYTHONPATH"] = os.pathsep.join([str(HARNESS), str(REPO / "src")])
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["TMPDIR"] = str(home)
            yield server, env, home
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _run(args: list[str], env: dict[str, str]) -> tuple[int, str]:
    command = [sys.executable, "-m", "splan", *args]
    session = PtySession(command, env=env, cwd=REPO)
    try:
        code = session.wait_exit(timeout=30)
        output = strip_ansi(session.transcript)
    finally:
        session.close()
    return (code if code is not None else -1), output


def test_suche_studiengang() -> None:
    with _fake_server("suche") as (_server, env, _home):
        code, output = _run(["suche", "Angewandte Informatik"], env)

    assert code == 0, output
    assert "Semester: Wintersemester 2026/2027" in output
    assert "Angewandte Informatik (AI)" in output
    assert "AI1 – AI 1. Semester" in output
    assert "AI2 – AI 2. Semester" in output
    assert "AI3 – AI 3. Semester" in output


def test_plan_woche() -> None:
    with _fake_server("plan") as (_server, env, _home):
        code, output = _run(["plan", "AI1"], env)

    assert code == 0, output
    assert "Plan AI1 – Woche 02.11.2026 bis 06.11.2026" in output
    assert "Montag, 02.11.2026" in output
    assert "08:00-09:30  Lineare Algebra und Computergrafik (173423)" in output
    assert "Raum A411 · Prof. Dr. A. Beispiel" in output
    assert "09:45-11:15  Freies Lernen" in output
    assert "Dienstag, 03.11.2026" in output
    assert "09:45-11:15  Informationssicherheit 1 (173431)" in output


def test_heute() -> None:
    with _fake_server("heute") as (_server, env, _home):
        code, output = _run(["heute", "AI1"], env)

    assert code == 0, output
    assert "Heute, Montag 02.11.2026 – AI1" in output
    assert "08:00-09:30  Lineare Algebra und Computergrafik (173423)" in output
    assert "Raum A411 · Prof. Dr. A. Beispiel" in output
    assert "09:45-11:15  Freies Lernen" in output


def test_raum() -> None:
    with _fake_server("raum") as (_server, env, _home):
        code, output = _run(["raum", "A411"], env)

    assert code == 0, output
    assert "Raum A411 – TechCampus HN" in output
    assert "Montag, 02.11.2026" in output
    assert "08:00-09:30  Lineare Algebra und Computergrafik (173423) · AI1" in output
    assert "11:30-13:00  Programmieren 1 (173411) · AI1" in output


def test_ics_export() -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    dest = SCRATCH / f"ai1-{uuid.uuid4().hex}.ics"
    relative = dest.relative_to(REPO)
    try:
        with _fake_server("ics") as (_server, env, _home):
            code, output = _run(["ics", "AI1", "--datei", str(relative)], env)

        assert code == 0, output
        assert f"ICal gespeichert: {relative}" in output
        assert "1 Termin" in output
        assert dest.is_file()
        assert "BEGIN:VCALENDAR" in dest.read_text(encoding="utf-8")
        assert "BEGIN:VEVENT" in dest.read_text(encoding="utf-8")
    finally:
        dest.unlink(missing_ok=True)


def test_standard_gruppe() -> None:
    with _fake_server("standard") as (_server, env, home):
        code, output = _run(["standard", "AI1"], env)
        config = home / ".config" / "splan-cli" / "config.json"

        assert code == 0, output
        assert "Standardgruppe gespeichert: AI1" in output
        assert config.is_file()
        assert "AI1" in config.read_text(encoding="utf-8")
