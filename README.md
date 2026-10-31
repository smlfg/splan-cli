# splan-cli

Stundenpläne der Hochschule Heilbronn aus StarPlan im Terminal: Studiengänge
und Semester per Name suchen, Wochen- und Tagesplan lesen, Raumbelegungen
prüfen und ICal-Dateien lokal speichern. Kein Login, nur öffentliche
Lese-Anfragen.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/splan-cli
splan suche "Angewandte Informatik"
splan plan AI1
splan heute AI1
splan raum A411
splan ics AI1 --datei scratch/tmp/ai1.ics
splan standard AI1
```

Semester und Planungseinheit wählt `splan` automatisch. Die vollständigen
Nutzer-Sitzungen, Routen und Fixtures stehen in [docs/UX.md](docs/UX.md).

## Befehle

```bash
splan suche "Angewandte Informatik"
splan plan AI1
splan plan AI1 --woche 45
splan plan AI1 --datum 2026-11-03
splan heute
splan heute AI1
splan raum A411
splan ics AI1
splan ics AI1 --datei scratch/tmp/ai1.ics
splan standard AI1
splan --json plan AI1
```

- `suche STUDIENGANG` findet Studiengänge und ihre Planungsgruppen.
- `plan GRUPPE` zeigt die aktuelle Woche, optional `--woche KW` oder
  `--datum JJJJ-MM-TT`.
- `heute [GRUPPE]` zeigt nur den heutigen Tag; ohne Argument gilt die
  Standardgruppe.
- `raum RAUMNAME` sucht den Raum über alle Standorte und zeigt die Belegung.
- `ics GRUPPE [--datei PFAD]` speichert den ICal-Export lokal.
- `standard GRUPPE` merkt sich eine Planungsgruppe für `heute` und `plan`.

Alle Unterkommandos haben `--help`. `--version` zeigt die Version. Mit
`--json` (oder wenn stdout kein Terminal ist) kommt genau ein JSON-Objekt.

## Konfiguration

Die Standardgruppe liegt in `$XDG_CONFIG_HOME/splan-cli/config.json`, sonst
in `~/.config/splan-cli/config.json`:

```json
{"standard_gruppe": "AI1"}
```

| Umgebungsvariable | Bedeutung |
|---|---|
| `SPLAN_BASE_URL` | Basis-URL, Standard `https://splan.hs-heilbronn.de/splan/` |
| `SPLAN_HEUTE` | Nur für Tests: heutiges Datum als `JJJJ-MM-TT` |
| `XDG_CONFIG_HOME` | Pfad zur Konfiguration |

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | Erfolg |
| 1 | Gruppe/Raum nicht gefunden oder mehrdeutig, keine Standardgruppe |
| 2 | Aufruf- oder Usage-Fehler |
| 3 | Netz- oder Quellenfehler |
| 4 | Zugriff verweigert oder Login nötig |

## Inoffiziell

`splan` ist ein inoffizielles Werkzeug und kein Angebot der Hochschule
Heilbronn. Es nutzt ausschließlich öffentlich lesbare StarPlan-Seiten. Die
Schnittstelle kann sich jederzeit ändern; maßgeblich sind die offiziellen
Aushänge. Live getestet wurden nur lesende GET-Anfragen.

## Entwicklung

Vor jeder Codezeile wird die UX-Spec geprüft:

```bash
python3 tests/harness/ux_check.py . --spec-only
```

Nach dem Bau müssen beide Gates grün sein:

```bash
python3 tests/harness/ux_check.py .
python3 tests/harness/ux_session.py .
```

`tests/harness/` wird unverändert aus dem Template übernommen.

## Lizenz

MIT, Copyright (c) 2026 smlfg. Siehe [LICENSE](LICENSE).
