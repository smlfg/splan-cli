# Anforderungen: splan

## Zweck

`splan` liest öffentliche Stundenplan-Daten der Hochschule Heilbronn aus
StarPlan (`https://splan.hs-heilbronn.de/splan/`) und zeigt sie im Terminal.
Ein Mensch findet Studiengang, Planungsgruppe und Raum per Namen, sieht
Wochen- und Tagesplan und speichert einen ICal-Export lokal. Es gibt keinen
Login und keine schreibende Web-Aktion.

## Nutzer-Aufgaben

1. **Studiengang suchen.** `splan suche "Angewandte Informatik"` findet
   Studiengänge und deren Planungsgruppen (Semester) per Namen. Die Ausgabe
   nennt Semester, Studiengang-Kürzel und Planungsgruppen.
2. **Wochenplan lesen.** `splan plan AI1` zeigt die aktuelle Woche (oder
   `--woche`/`--datum`) mit Wochentag, Zeit, Veranstaltung, Raum und Dozent.
3. **Heutigen Plan lesen.** `splan heute AI1` zeigt nur den heutigen Tag.
   Ohne Argument wird die gespeicherte Standardgruppe verwendet.
4. **Raumbelegung prüfen.** `splan raum A411` sucht den Raum über alle
   Standorte und zeigt seine Belegung mit Planungsgruppe.
5. **ICal exportieren.** `splan ics AI1 --datei pfad.ics` lädt den
   StarPlan-ICal-Link herunter und speichert ihn lokal.
6. **Standardgruppe merken.** `splan standard AI1` speichert die
   Planungsgruppe in der Konfiguration, damit `heute` und `plan` ohne
   Argument funktionieren.

Jede Aufgabe ist in `docs/UX.md` als abtippbare Terminal-Sitzung mit
erwarteter Ausgabe festgehalten und hat mindestens einen Akzeptanztest unter
`tests/acceptance/`.

## Nachfrage

- Quelle: `./scratch/ref/NEXT20.md`, Nachfrage-Check nach dem
  demand-first-gate, Stand **30.10.2026**, Platz 2.
- Ergebnis: **GO (Eigenbedarf)**. Für StarPlan wurde **keine CLI und kein
  MCP-Server** gefunden; die externe Nachfrage ist schwach. Der Bau ist
  durch den Eigenbedarf an einem Terminal-Stundenplan gerechtfertigt.
- Die Seite liefert öffentlich HTML und ICal-Links und ist ohne Login
  lesbar.

## Datenquelle

StarPlan der Hochschule Heilbronn, Basis-URL
`https://splan.hs-heilbronn.de/splan/` (überschreibbar über
`SPLAN_BASE_URL`). Genutzte, ausschließlich lesende Endpunkte:

| Zweck | Request |
|---|---|
| Semester | `GET json?m=getpus` |
| Studiengänge | `GET json?m=getogs&pu=<id>` |
| Planungsgruppen | `GET json?m=getPgsExt&pu=<id>&og=<id>` |
| Standorte | `GET json?m=getlocs` |
| Räume je Standort | `GET json?m=getros&loc=<id>` |
| Wochen-/Raumplan | `GET json?m=getTT&sel=pg\|ro&...` |
| ICal Planungsgruppe | `GET ical?lan=de&puid=<id>&type=pg&pgid=<id>` |
| ICal Raum | `GET ical?lan=de&puid=<id>&type=room&roomid=<id>` |

Semester und Planungseinheit wählt das Tool automatisch (aktuelles Semester
aus `getpus`). Die Roh-Erkundung ist in `scratch/live/NOTIZEN.md`
dokumentiert; Fixtures liegen anonymisiert unter `tests/fixtures/ux/`.

## Grenzen

- **Inoffiziell.** Die Schnittstelle ist nicht dokumentiert und kann sich
  jederzeit ändern. `splan` ist kein Angebot der Hochschule Heilbronn.
- **Nur lesend live getestet.** Alle Live-Aufrufe waren GET-Requests auf
  öffentliche Seiten. Es gibt keinen Login, keine Reservation und keine
  schreibende Aktion.
- **Keine Garantie auf Vollständigkeit.** Das Tool zeigt, was StarPlan
  öffentlich im gewählten Semester liefert; Änderungen, Ausfälle und
  Raumwechsel sind möglich.
- **HTML-Fragmente statt API.** `getTT` liefert nur ein HTML-Fragment; das
  Parsen stützt sich auf stabile Klassen (`ttevent`, `tooltip`,
  `ttweekdaycell`).
- **Testbarkeit.** `SPLAN_BASE_URL` zeigt auf den Fake-Server,
  `SPLAN_HEUTE` (nur Tests) macht datumsabhängige Ausgaben deterministisch.
- **Kein Ersatz für verbindliche Aushänge.** Maßgeblich sind die
  offiziellen Informationen der Hochschule.

## Nicht im Scope

- Login, persönliche Pläne (`sel=le`, `me`) oder schreibende Aktionen.
- Raumfreie Suche (`searchRooms`) und Repräsentations-/Belegungsplanung.
- Push, Kalender-Synchronisation oder dauerhaftes Caching.
- Garantierte Verfügbarkeit oder eine offizielle API.

## Akzeptanzkriterien

- `python3 tests/harness/ux_check.py . --spec-only` endet mit Exit 0.
- Jede Sitzung aus `docs/UX.md` hat einen Akzeptanztest in
  `tests/acceptance/test_ux_sessions.py`, der das Tool als Subprozess gegen
  `tests/harness/fake_server.py` startet.
- Exit-Codes, Flags und Ausgabeformate entsprechen `INTERFACE.md`.
- README-Schnellstart enthält wörtlich die Befehle der UX-Sitzungen.
- Keine Tracebacks, auch nicht bei Strg+C/EOF; Fehler nennen den nächsten
  Schritt.
