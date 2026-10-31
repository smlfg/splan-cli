# UX-Spec: splan

`splan` zeigt Stundenpläne der Hochschule Heilbronn aus StarPlan im Terminal.
Die Seite ist öffentlich: Es gibt keinen Login und keine schreibende
Web-Aktion. Alle Befehle sind so abtippbar, wie ein Mensch sie im Terminal
eingibt. Semester und Planungseinheit wählt das Tool automatisch.

## Meta

Das Meta-Objekt benennt den Befehlsnamen im PATH, den Installationsbefehl und
alle Umgebungsvariablen. `SPLAN_BASE_URL` überschreibt die Basis-URL für den
Fake-Server. `SPLAN_HEUTE` macht die datumsabhängigen Sitzungen für Tests
deterministisch.

```ux-meta
{"tool": "splan",
 "install": "pipx install git+https://github.com/smlfg/splan-cli",
 "base_url_env": "SPLAN_BASE_URL",
 "env": {"SPLAN_HEUTE": "2026-11-02"}}
```

## Sitzungen

Jede Sitzung ist eine Nutzer-Aufgabe. `$` ist ein Befehl, `>` eine Eingabe,
`<` eine erwartete Ausgabe und `!` der erwartete Exit-Code. Der
Installationsbefehl wird von der Harness durch eine lokale Installation in ein
frisches venv ersetzt.

### Installation und Studiengang suchen

Der Suchbegriff ist positional. Die Ausgabe nennt Studiengang und
Planungsgruppe, damit ein Mensch ohne Nachschlagen weiterarbeiten kann.

```ux-session
$ pipx install git+https://github.com/smlfg/splan-cli
$ splan suche "Angewandte Informatik"
< Semester: Wintersemester 2026/2027
< Angewandte Informatik (AI)
< AI1 – AI 1. Semester
< AI2 – AI 2. Semester
< AI3 – AI 3. Semester
! exit 0
```

### Stundenplan einer Planungsgruppe

`plan` nimmt den Namen der Planungsgruppe positional. Ohne weitere Option
zeigt das Tool die aktuelle Woche; die Ausgabe nennt Zeit, Veranstaltung,
Raum und Dozent.

```ux-session
$ splan plan AI1
< Plan AI1 – Woche 02.11.2026 bis 06.11.2026
< Montag, 02.11.2026
< 08:00-09:30  Lineare Algebra und Computergrafik (173423)
< Raum A411 · Prof. Dr. A. Beispiel
< 09:45-11:15  Freies Lernen
< Raum E116
< Dienstag, 03.11.2026
< 09:45-11:15  Informationssicherheit 1 (173431)
< Raum E219 · M. Muster
! exit 0
```

### Heutiger Stundenplan

`heute` ist die Kurzform für den aktuellen Tag. Die Sitzung nutzt
`SPLAN_HEUTE` aus dem Meta-Block, damit die erwartete Ausgabe zu den Fixtures
passt.

```ux-session
$ splan heute AI1
< Heute, Montag 02.11.2026 – AI1
< 08:00-09:30  Lineare Algebra und Computergrafik (173423)
< Raum A411 · Prof. Dr. A. Beispiel
< 09:45-11:15  Freies Lernen
< Raum E116
! exit 0
```

### Raumbelegung

`raum` sucht den Raum per Namen über alle Standorte und zeigt seine Belegung.
Die Raum-ID muss ein Mensch nicht kennen.

```ux-session
$ splan raum A411
< Raum A411 – TechCampus HN
< Montag, 02.11.2026
< 08:00-09:30  Lineare Algebra und Computergrafik (173423) · AI1
< 11:30-13:00  Programmieren 1 (173411) · AI1
! exit 0
```

### ICal exportieren

`ics` lädt den ICal-Link von StarPlan herunter und speichert ihn lokal. Das
Ziel wird mit `--datei` angegeben; ohne die Option landet die Datei im
aktuellen Verzeichnis.

```ux-session
$ splan ics AI1 --datei scratch/tmp/ai1.ics
< ICal gespeichert: scratch/tmp/ai1.ics
< 1 Termin
! exit 0
```

### Standardgruppe speichern

`standard` merkt sich eine Planungsgruppe in der Konfiguration, damit
`heute` und `plan` ohne Argument funktionieren.

```ux-session
$ splan standard AI1
< Standardgruppe gespeichert: AI1
! exit 0
```

## Lesende Routen

Hier stehen alle Routen, die die Sitzungen gegen den Fake-Server brauchen.
`path` wird ohne Querystring exakt verglichen; `query_contains` ist optional.
Die Basis-URL kommt aus `SPLAN_BASE_URL`, die Antwortdateien liegen relativ
zum Repo.

```ux-routes
[{"method":"GET","path":"/json","query_contains":"m=getpus","response":"tests/fixtures/ux/getpus.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"m=getogs","response":"tests/fixtures/ux/getogs.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"m=getPgsExt","response":"tests/fixtures/ux/getpgs_ai.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"sel=ro","response":"tests/fixtures/ux/gettt_room_a411.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"m=getTT","response":"tests/fixtures/ux/gettt_ai1.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"m=getlocs","response":"tests/fixtures/ux/getlocs.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"loc=2","response":"tests/fixtures/ux/getros_loc2.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/json","query_contains":"m=getros","response":"tests/fixtures/ux/getros_empty.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/ical","response":"tests/fixtures/ux/ical_ai1.ics","status":200,"content_type":"text/calendar; charset=utf-8"}]
```

## Schreibende Aktionen

`splan` hat keine schreibende Web-Aktion. Es gibt daher keine
`ux-formsteps`, keine Bestätigungsfrage `[j/N]` und keine
`credential_env`-Variablen.
