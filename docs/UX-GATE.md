# UX-Gate-Bericht

- Datum: 2026-10-31
- Tool: `splan`
- Repo: `smlfg/splan-cli`

## Ergebnis

| Prüfung | Befehl | Exit-Code |
|---|---|---|
| Statisches UX-Gate | `python3 tests/harness/ux_check.py . --report scratch/ux_check.md` | 0 (PASS) |
| PTY-Sitzungen | `python3 tests/harness/ux_session.py . --report scratch/ux_session.md` | 0 (PASS) |

Zusätzlich: `scratch/venv/bin/pytest -q` → 57 passed.

## ux_check.py

| ID | Ergebnis | Befund |
|---|---|---|
| UX00 | PASS | 35 Request(s) am Fake-Server, keine Fremdverbindung |
| UX01 | PASS | docs/UX.md: 6 Sitzungen, 0 formsteps |
| UX02 | PASS | keine Credential-Env-Variablen gefunden |
| UX03 | PASS | --help, --version und 6 Unterkommandos mit Exit 0 |
| UX04 | PASS | 6 Unterkommandos ohne Pflicht-Option statt positional |
| UX05 | PASS | 6 Sitzungen ohne JSON/Traceback im TTY |
| UX06 | PASS | Schnellstart: 6 Tool-Befehle, Installation passt |
| UX07 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX08 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX09 | SKIP | keine schreibende Sitzung |

## ux_session.py

| Sitzung | Lauf | Ergebnis | Befund |
|---|---|---|---|
| Installation und Studiengang suchen | 1 | PASS | OK |
| Stundenplan einer Planungsgruppe | 1 | PASS | OK |
| Heutiger Stundenplan | 1 | PASS | OK |
| Raumbelegung | 1 | PASS | OK |
| ICal exportieren | 1 | PASS | OK |
| Standardgruppe speichern | 1 | PASS | OK |

Hinweis: `ux_check.py` und `ux_session.py` verwenden standardmäßig dasselbe
venv (`scratch/ux-venv`). Sie müssen nacheinander laufen, sonst kann ein
gleichzeitiger Lauf das venv des anderen löschen.
