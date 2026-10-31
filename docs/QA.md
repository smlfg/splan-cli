# Pflicht-QA – splan-cli

- Datum: 2026-10-31
- Version: 0.1.0, Commit `2e08172` (`docs(ux): UX-Gate-Bericht`)
- Installiert als: `pipx install git+https://github.com/smlfg/splan-cli`
  (frische Umgebung, Protokoll `scratch/qa/pipx-install.log`); geprüfte
  Binary `scratch/pipx/bin/splan`, Quellcode identisch mit Commit `2e08172`
  (Diff: nur `__pycache__`).
- Aufrufe live (nur lesende GET-Requests auf https://splan.hs-heilbronn.de/splan/)
  im Pseudo-Terminal (`script -q`), Belege unter `scratch/qa/`.

| Nr | Prüfung | Befehl | Erwartet | Ergebnis | Beleg |
|---|---|---|---|---|---|
| 01 | Frische pipx-Installation | `pipx install git+https://github.com/smlfg/splan-cli` | Installation meldet App `splan` | OK | scratch/qa/pipx-install.log |
| 02 | `--version` | `splan --version` | `splan 0.1.0`, Exit 0 | OK | scratch/qa/version.log |
| 03 | `--help` verständlich | `splan --help` | Nutzungstext mit Unterkommandos, Exit 0 | OK | scratch/qa/help.log |
| 04 | Ohne Kommando | `splan` | Help plus „Nächster Schritt“, kein Traceback | OK | scratch/qa/ohne-kommando.log |
| 05 | Unbekanntes Kommando | `splan quatsch` | Fehler + nächster Schritt, Exit 2 | OK | scratch/qa/unbekannt.log |
| 06 | Fehlendes Pflicht-Argument | `splan suche` | Fehler + nächster Schritt, kein Traceback | OK | scratch/qa/fehlendes-arg.log |
| 07 | Studiengang suchen (README-Zeile, TTY) | `splan suche "Angewandte Informatik"` | Semester + AI-Planungsgruppen in Klartext | OK | scratch/qa/suche-tty.log/json-suche.json |
| 08 | Suche JSON valide | `splan --json suche K` | genau ein JSON, `ok: true` | OK | scratch/qa/json-suche-k.json |
| 09 | Leeres Suchergebnis | `splan suche Quantenphilosophie` | „Kein Studiengang gefunden …“, Exit 1 | OK | scratch/qa/suche-leer.log |
| 10 | Suche mit Umlauten | `splan suche "Künstliche"` | Treffer AKI/KID | **FAIL** | scratch/qa/qa-r2-suche-umlaut-true.log; json-suche-k.json zeigt Namen mit Ersetezeichen „K�nstliche“ |
| 11 | Wochenplan aktuelle Woche (TTY) | `splan plan AI1` | Tage/Zeiten/Räume/Dozenten Klartext | OK | scratch/qa/plan-tty.log/json-plan.json |
| 12 | Filter `--woche 45` | `splan plan AI1 --woche 45` | Header „Woche 02.11.–06.11.2026“ (KW 45 korrekt) | OK | scratch/qa/plan-woche-tty.log |
| 13 | Filter `--datum` | `splan plan AI1 --datum 2026-11-03` | Tag „Dienstag, 03.11.2026“ im Wochenkontext | OK | scratch/qa/plan-datum-tty.log |
| 14 | Datumsfilter über alle Treffer | JSON von 11–13 | alle Einträge innerhalb der angezeigten Woche | OK (16/16 Kontrollen) | scratch/qa/json-plan.json (Tage ⊆ 26.–30.10.2026) |
| 15 | Raumfilter über alle Treffer | `splan raum A411` | jeder Treffereintrag Raum A411 | OK (16/16 Kontrollen) | scratch/qa/json-raum.json (0 Ausreißer) |
| 16 | `plan` ohne Standardgruppe | `splan plan` | „Keine Standardgruppe …“ + nächster Schritt | OK | scratch/qa/plan-keine-standard.log |
| 17 | Mehrdeutige Gruppe | `splan plan AI` | Auflistung der Kandidaten + nächster Schritt | OK | scratch/qa/plan-mehrdeutig.log |
| 18 | Unbekannte Gruppe | `splan plan AI9` | „nicht gefunden“ + `splan suche AI9` | OK | scratch/qa/plan-unbekannt.log |
| 19 | Woche außerhalb 1–53 | `splan plan AI1 --woche 99` | Warnung + gültigen Bereich nennen | OK | scratch/qa/plan-woche99.log |
| 20 | `--woche` + `--datum` gemeinsam | `splan plan AI1 --woche 45 --datum 2026-11-03` | Fehler „schließen sich aus“ | OK | scratch/qa/plan-konflikt.log |
| 21 | Woche außerhalb des Semesters | `splan plan AI1 --datum 2027-03-01` | Hinweis auf Semester + gültigen Zeitraum | OK | scratch/qa/plan-ausserhalb.log |
| 22 | `heute` (Samstag) | `splan heute AI1` | „Keine Veranstaltungen“ am Wochenplan-freien Tag | OK | scratch/qa/heute-tty.log |
| 23 | `heute` mit `SPLAN_HEUTE=2026-11-03` | `env SPLAN_HEUTE=2026-11-03 splan heute AI1` | nur Dienstag-Einträge (stimmt mit Wochenplan aus Zeile 13 überein) | OK | scratch/qa/heute-dienstag.log |
| 24 | Bekannter/Default-Heute via `--json` | `splan --json heute` (Standardgruppe gespeichert) | JSON mit Standardgruppe AI1 | OK | scratch/qa/json-heute-standard.json |
| 25 | Ungültiges `SPLAN_HEUTE` | `env SPLAN_HEUTE=31.10.2026 splan heute AI1` | Format „JJJJ-MM-TT“ erläutert | OK | scratch/qa/heute-fehler.log |
| 26 | Raumbefehl TTY/JSON | `splan raum A411` | Belegwoche in Klartext | OK | scratch/qa/raum-tty.log/json-raum.json |
| 27 | Mehrdeutiger Raum | `splan raum A4` | SA401–SA409 aufgelistet + nächster Schritt | OK | scratch/qa/raum-mehrdeutig.log |
| 28 | Unbekannter Raum | `splan raum ZZZ999` | „nicht gefunden“ + weiterer Hinweis | OK | scratch/qa/raum-unbekannt.log |
| 29 | ICal-Export | `splan ics AI1 --datei scratch/tmp/qa-ai1.ics` | „ICal gespeichert“ + Terminanzahl | OK | scratch/qa/ics-tty.log (`BEGIN:VCALENDAR`, 181 `BEGIN:VEVENT`) |
| 30 | ICal JSON valide | `splan --json ics AI1` | JSON `ok: true`, `termine: 181` | OK | scratch/qa/json-ics.json |
| 31 | Zielverzeichnis fehlt | `splan ics AI1 --datei scratch/tmp/gibt-es-nicht/x.ics` | Verzeichnismeldung + weiterer Schritt | OK | scratch/qa/ics-pfad.log |
| 32 | Unbekannte Gruppe bei `ics` | `splan ics AI9` | „nicht gefunden“ + `splan suche` | OK | scratch/qa/ics-unbekannt.log |
| 33 | Standardgruppe speichern | `splan standard AI1` | Bestätigung in Klartext | OK | scratch/qa/standard-tty.log |
| 34 | Standardgruppe wirkt für `heute` | `splan heute` (Standard gespeichert) | „Heute … – AI1“ | OK | scratch/qa/heute-standard-tty.log |
| 35 | standard JSON valide | `splan --json standard AI1` | JSON mit Pfad der Config | OK | scratch/qa/json-standard.json |
| 36 | Netzfehler (verweigerte Verbindung) | `env SPLAN_BASE_URL=http://127.0.0.1:9/splan/ splan suche Informatik` | Fehler + nächster Schritt, Exit 3, kein Traceback | OK | scratch/qa/netz-fehler.log |
| 37 | Ungültige `SPLAN_BASE_URL` | `env SPLAN_BASE_URL=nicht-url splan suche Informatik` | Hinweis vollständige URL angeben | OK | scratch/qa/url-fehler.log |
| 38 | Netz-Live-Ausfall (SSL-Timeout) | `splan suche` im Ausfall-Fenster | Meldung, kein Traceback | OK | scratch/tmp/qa-r2/suche-umlaut.err + json-heute-dienstag.json („ok“: false) |
| 39 | TTY liefert Text, Pipe liefert JSON | `splan plan AI1 > datei.json` | genau ein JSON-Objekt | OK | scratch/qa/plan.json |
| 40 | Kaputte Konfiguration | `env XDG_CONFIG_HOME=… splan heute` mit binär-verfälschter `config.json` | Fehler + nächster Schritt | **FAIL** | scratch/qa/config-kaputt.log + qa-r2-config-kaputt.log (Traceback + `NameError: name 'SourceError' is not defined`) |
| 41 | Kaputte Konfiguration mit `--json` | `env XDG_CONFIG_HOME=… splan --json heute` | valides JSON auf stdout | **FAIL** | scratch/qa/config-kaputt-json.out (leer) + config-kaputt-json.err (Traceback) — stdout ohne JSON |

## Zählung

- Prüfungen: 41
- OK: 38
- FAIL: 3 (Zeilen 10, 40, 41; 40/41 sind derselbe Codefehler in zwei Betriebsarten)
- SKIP: 0

## Offene FAILs

1. **Umlaut-Auflösung in der Suche** (Zeile 10): StarPlans JSON-Endpunkte
   (`getogs`, `getPgsExt`) antworten in windows-1252/ISO-8859-1. Der Client
   dekodiert mit `utf-8-sig` und `errors="replace"` (`splan/client.py`,
   `_get_json`), dadurch Namen mit U+FFFD-Ersetezeichen und Suche nach
   „Künstliche“ ohne Treffer. Beleg raw GET: `getogs`/`getPgsExt` enthalten
   Byte 0xfc (ü), sind kein gültiges UTF-8.
2. **Kaputte Konfiguration erzeugt Traceback** (Zeilen 40/41): `config.py::_lesen`
   behandelt `UnicodeDecodeError` nicht; in `cli.py::main` läuft die Ausnahme
   in den Fallback auf `SourceError(...)` (Zeile 475), was mit
   `NameError: name 'SourceError' is not defined` endet — der Fallback
   importiert `SourceError` nicht. Nutzer sieht doppelten Traceback,
   in `--json` bleibt stdout leer.
