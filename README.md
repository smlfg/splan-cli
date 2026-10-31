# splan-cli

Stundenpläne der Hochschule Heilbronn aus StarPlan im Terminal: Studiengänge
und Semester per Name suchen, Wochenplan und Tagesplan lesen, Raumbelegungen
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

Die vollständigen Nutzer-Sitzungen, Routen und Fixtures stehen in
[docs/UX.md](docs/UX.md).

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
