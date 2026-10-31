# Interface: splan

Kommandozeilen-Vertrag für `splan`. Maßgeblich sind die hier genannten
Flags, Ausgabeformate und Exit-Codes. Abweichungen sind Fehler.

## Aufruf

```
splan [--json] <unterkommando> [argumente ...]
```

Ohne Unterkommando gibt `splan` die Hilfe aus und endet mit Exit 2.

Globale Optionen:

| Option | Wirkung |
|---|---|
| `--json` | genau ein JSON-Objekt auf stdout; Prompts und Fehlertexte auf stderr |
| `--version` | Version ausgeben, Exit 0 |
| `--help` | Hilfe ausgeben, Exit 0 (auch für jedes Unterkommando) |

Ausgabeformat: Im Terminal (stdout ist ein TTY) menschenlesbarer Text. Ist
stdout kein TTY oder ist `--json` gesetzt, wird JSON ausgegeben. Fehler im
Textmodus gehen nach stderr, im JSON-Modus als Fehlerobjekt nach stdout.
Tracebacks werden nie ausgegeben.

## Unterkommandos

### `splan suche STUDIENGANG`

Sucht ohne Beachtung der Groß-/Kleinschreibung in Name und Kürzel der
Studiengänge des aktuellen Semesters. `STUDIENGANG` ist positional und
Pflicht. Die Suche liefert alle Treffer mit ihren Planungsgruppen.

Textausgabe:

```
Semester: Wintersemester 2026/2027
Angewandte Informatik (AI)
AI1 – AI 1. Semester
AI2 – AI 2. Semester
AI3 – AI 3. Semester
```

Kein Treffer: Exit 1 mit Hinweis, einen anderen Suchbegriff zu verwenden.

JSON:

```json
{"ok": true, "semester": {"id": 48, "shortname": ".WS 2026/2027",
 "name": "Wintersemester 2026/2027"},
 "treffer": [{"id": 725, "shortname": "AI", "name": "Angewandte Informatik",
 "planungsgruppen": [{"id": 30350, "shortname": "AI1",
 "name": "AI 1. Semester"}]}]}
```

### `splan plan GRUPPE [--woche KW | --datum JJJJ-MM-TT]`

Zeigt den Plan einer Planungsgruppe für eine Woche. `GRUPPE` ist positional
und akzeptiert Kürzel (`AI1`) oder Namen (`AI 1. Semester`). Ohne
Wochenoption gilt die aktuelle Woche; `SPLAN_HEUTE` verschiebt „heute“ nur
im Test.

- `--woche KW`: Kalenderwoche nach ISO 8601; die Woche beginnt montags.
- `--datum JJJJ-MM-TT`: ein Tag in der gewünschten Woche.
- `--woche` und `--datum` schließen sich aus (Exit 2).

Textausgabe:

```
Plan AI1 – Woche 02.11.2026 bis 06.11.2026
Montag, 02.11.2026
08:00-09:30  Lineare Algebra und Computergrafik (173423)
Raum A411 · Prof. Dr. A. Beispiel
09:45-11:15  Freies Lernen
Raum E116
Dienstag, 03.11.2026
09:45-11:15  Informationssicherheit 1 (173431)
Raum E219 · M. Muster
```

Tage ohne Veranstaltung werden ausgelassen. Ist die Gruppe unbekannt oder
mehrdeutig, nennt der Fehler `splan suche <begriff>` als nächsten Schritt
(Exit 1). Ist die Woche außerhalb des Semesters, Exit 1 mit Hinweis auf
`--woche`/`--datum`.

JSON:

```json
{"ok": true,
 "gruppe": {"id": 30350, "shortname": "AI1", "name": "AI 1. Semester"},
 "semester": {"id": 48, "name": "Wintersemester 2026/2027"},
 "woche": {"von": "2026-11-02", "bis": "2026-11-06"},
 "tage": [{"datum": "2026-11-02", "wochentag": "Montag",
 "veranstaltungen": [{"start": "08:00", "ende": "09:30",
 "titel": "Lineare Algebra und Computergrafik", "import_id": "173423",
 "raum": "A411", "dozent": "Prof. Dr. A. Beispiel",
 "gruppe": "AI1"}]}]}
```

### `splan heute [GRUPPE]`

Kurzform für den heutigen Tag. Ohne `GRUPPE` wird die Standardgruppe aus der
Konfiguration verwendet; ist keine gesetzt, Exit 1 mit Hinweis
`splan standard GRUPPE`.

Textausgabe:

```
Heute, Montag 02.11.2026 – AI1
08:00-09:30  Lineare Algebra und Computergrafik (173423)
Raum A411 · Prof. Dr. A. Beispiel
09:45-11:15  Freies Lernen
Raum E116
```

Ohne Veranstaltungen: dieselbe Kopfzeile, danach `Keine Veranstaltungen.`
und Exit 0.

JSON: wie `plan`, zusätzlich `"heute": "2026-11-02"` und `"tage"` mit genau
einem Tag.

### `splan raum RAUMNAME`

Sucht den Raum per Kürzel oder Namen über alle Standorte (`getlocs` +
`getros`) und zeigt seine Belegung für die aktuelle Woche. `RAUMNAME` ist
positional und Pflicht. Exakter Kürzel-Treffer hat Vorrang vor
Teilstring-Treffern.

Textausgabe:

```
Raum A411 – TechCampus HN
Montag, 02.11.2026
08:00-09:30  Lineare Algebra und Computergrafik (173423) · AI1
11:30-13:00  Programmieren 1 (173411) · AI1
```

Kein oder mehrere nicht eindeutige Treffer: Exit 1 mit den Kandidaten und
dem Hinweis, den Raumnamen zu präzisieren.

JSON:

```json
{"ok": true,
 "raum": {"id": 71, "shortname": "A411", "name": "Beamer, Tafel, OHP",
 "standort": {"id": 2, "shortname": "TechCampus HN", "name": "74081"}},
 "woche": {"von": "2026-11-02", "bis": "2026-11-06"},
 "tage": [{"datum": "2026-11-02", "wochentag": "Montag",
 "veranstaltungen": [{"start": "08:00", "ende": "09:30",
 "titel": "Lineare Algebra und Computergrafik", "import_id": "173423",
 "raum": "A411", "dozent": "Prof. Dr. A. Beispiel",
 "gruppe": "AI1"}]}]}
```

### `splan ics GRUPPE [--datei PFAD]`

Lädt den ICal-Link der Planungsgruppe und speichert ihn lokal. Ohne
`--datei` wird `<GRUPPE>.ics` im aktuellen Verzeichnis angelegt. Das
Zielverzeichnis muss existieren; sonst Exit 1 mit Pfad-Hinweis.

Textausgabe:

```
ICal gespeichert: scratch/tmp/ai1.ics
1 Termin
```

Bei mehreren Terminen: `<n> Termine`.

JSON:

```json
{"ok": true, "datei": "scratch/tmp/ai1.ics", "termine": 1,
 "gruppe": {"id": 30350, "shortname": "AI1", "name": "AI 1. Semester"}}
```

### `splan standard GRUPPE`

Prüft die Gruppe wie `plan` und speichert ihr Kürzel als Standardgruppe.
Textausgabe: `Standardgruppe gespeichert: AI1`.

JSON:

```json
{"ok": true, "standardgruppe": "AI1",
 "config": "/home/beispiel/.config/splan-cli/config.json"}
```

## Konfiguration

- Pfad: `$XDG_CONFIG_HOME/splan-cli/config.json`, sonst
  `~/.config/splan-cli/config.json`.
- Inhalt: `{"standard_gruppe": "AI1"}`. Weitere Schlüssel sind erlaubt und
  werden beim Schreiben erhalten.
- Die Datei wird mit Rechten 0600 angelegt. Sie enthält keine Geheimnisse
  und keine Personendaten.
- Ein explizit übergebenes `GRUPPE`-Argument hat Vorrang vor der
  Standardgruppe.

## Umgebungsvariablen

| Variable | Bedeutung |
|---|---|
| `SPLAN_BASE_URL` | Basis-URL, Standard `https://splan.hs-heilbronn.de/splan/`. Für den Fake-Server überschreiben. |
| `SPLAN_HEUTE` | Nur für Tests: heutiges Datum als `JJJJ-MM-TT`, überschreibt das Systemdatum für `plan`, `heute` und `raum`. |
| `XDG_CONFIG_HOME` | Standardpfad für die Konfiguration. |
| `NO_COLOR` | Deaktiviert Farbausgabe, sofern Farbe verwendet wird. |

Ungültige Werte (unparsebares Datum, ungültige URL) führen zu Exit 2 mit
einer verständlichen Meldung, nie zu einem Traceback.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Erfolg (auch „keine Veranstaltungen“) |
| 1 | Fachlicher Fehler: Gruppe/Raum nicht gefunden, mehrdeutig, keine Standardgruppe, Datei nicht schreibbar |
| 2 | Aufruf-/Usage-Fehler: unbekanntes Unterkommando, fehlendes Argument, ungültige Env-/Config-Werte, widersprüchliche Flags |
| 3 | Netz-/Quellenfehler: Timeout, Verbindungsfehler, HTTP-Status außer 2xx, unerwartetes/defektes JSON oder HTML |
| 4 | Zugriff verweigert oder Login nötig (HTTP 401/403) |

Bei Exit ≠ 0 nennt die Textausgabe den nächsten Schritt. Mit `--json` oder
ohne TTY steht auf stdout genau ein Objekt, zum Beispiel:

```json
{"ok": false, "fehler": "Gruppe 'AI9' nicht gefunden.",
 "naechster_schritt": "splan suche AI ausführen"}
```

## Nicht vorgesehen

- `login`/`logout`/`whoami`: StarPlan ist für diese Funktionen öffentlich.
- Schreibende Web-Aktionen, Formulare oder Bestätigungsfragen `[j/N]`.
- IDs als Pflichtargumente: Menschen geben Namen oder Kürzel ein.
