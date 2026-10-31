"""Parser für das HTML-Fragment von StarPlan ``getTT``."""

from __future__ import annotations

import re
from datetime import date, datetime
from html.parser import HTMLParser

from .dates import wochentag
from .models import Tag, Veranstaltung

TIME_RE = re.compile(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})")
IMPORT_RE = re.compile(r"^(.*?)\s*\((\d+)\)\s*$")
PX_RE = re.compile(r"(left|width)\s*:\s*(-?\d+(?:\.\d+)?)px", re.I)


def _style_px(style: str, name: str) -> float | None:
    for match in PX_RE.finditer(style or ""):
        if match.group(1).lower() == name:
            return float(match.group(2))
    return None


def _norm_time(value: str) -> str:
    hour, minute = value.split(":", 1)
    return f"{int(hour):02d}:{minute}"


def _parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


class _TimetableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[dict] = []
        self.events: list[dict] = []
        self._cell: dict | None = None
        self._cell_depth = 0
        self._cell_capture: str | None = None
        self._cell_parts: list[str] = []
        self._event: dict | None = None
        self._event_depth = 0
        self._tooltip = False
        self._tooltip_depth = 0
        self._line_parts: list[str] = []

    def _commit_line(self) -> None:
        text = "".join(self._line_parts).strip()
        self._line_parts = []
        if text and self._event is not None:
            self._event["lines"].append(text)

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {name: value or "" for name, value in attrs}
        classes = values.get("class", "").split()
        if self._cell is not None:
            if tag == "div":
                self._cell_depth += 1
            elif tag == "span":
                if "ttdaytext" in classes:
                    self._cell_capture = "weekday"
                    self._cell_parts = []
                elif values.get("data-date"):
                    self._cell["date"] = values["data-date"]
            return
        if tag == "div" and "ttweekdaycell" in classes:
            self._cell = {
                "left": _style_px(values.get("style", ""), "left"),
                "width": _style_px(values.get("style", ""), "width"),
                "date": None,
                "weekday": "",
            }
            self._cell_depth = 1
            return
        if self._event is not None:
            if tag == "div":
                self._event_depth += 1
                if "tooltip" in classes:
                    self._tooltip = True
                    self._tooltip_depth = self._event_depth
                    self._line_parts = []
            elif tag == "br" and self._tooltip:
                self._commit_line()
            return
        if tag == "div" and "ttevent" in classes:
            self._event = {
                "left": _style_px(values.get("style", ""), "left"),
                "lines": [],
            }
            self._event_depth = 1
            self._tooltip = False
            self._tooltip_depth = 0

    def handle_endtag(self, tag: str) -> None:
        if self._cell is not None:
            if tag == "span" and self._cell_capture:
                text = "".join(self._cell_parts).strip()
                if self._cell_capture == "weekday":
                    self._cell["weekday"] = text
                self._cell_capture = None
                self._cell_parts = []
            elif tag == "div":
                self._cell_depth -= 1
                if self._cell_depth <= 0:
                    self.cells.append(self._cell)
                    self._cell = None
            return
        if self._event is not None and tag == "div":
            if self._tooltip and self._event_depth == self._tooltip_depth:
                self._commit_line()
                self._tooltip = False
            self._event_depth -= 1
            if self._event_depth <= 0:
                self.events.append(self._event)
                self._event = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None and self._cell_capture:
            self._cell_parts.append(data)
            return
        if self._event is not None and self._tooltip:
            self._line_parts.append(data)


def _parse_tooltip(lines: list[str]) -> Veranstaltung | None:
    cleaned = [line.strip() for line in lines if line and line.strip()]
    time_index = None
    match = None
    for index in range(len(cleaned) - 1, -1, -1):
        match = TIME_RE.search(cleaned[index])
        if match is not None:
            time_index = index
            break
    if time_index is None or match is None:
        return None
    before = cleaned[:time_index]
    if len(before) >= 3:
        raum = before[-1]
        gruppe = before[-2]
        rest = before[:-2]
    elif len(before) == 2:
        raum = before[-1]
        gruppe = ""
        rest = before[:-1]
    elif len(before) == 1:
        raum = ""
        gruppe = ""
        rest = before
    else:
        return None
    titel = rest[0].strip() if rest else ""
    dozent = " ".join(rest[1:]).strip()
    import_id = ""
    title_match = IMPORT_RE.match(titel)
    if title_match is not None:
        titel = title_match.group(1).strip()
        import_id = title_match.group(2)
    return Veranstaltung(
        start=_norm_time(match.group(1)),
        ende=_norm_time(match.group(2)),
        titel=titel,
        import_id=import_id,
        raum=raum,
        dozent=dozent,
        gruppe=gruppe,
    )


def _day_for_left(
    left: float | None,
    cells: list[tuple[dict, date]],
    fallback: list[date] | None,
) -> date | None:
    if cells:
        if left is not None:
            for cell, day in cells:
                cell_left = cell.get("left")
                width = cell.get("width") or 180.0
                if cell_left is not None and cell_left <= left < cell_left + width:
                    return day
        if left is not None:
            return min(
                cells, key=lambda item: abs((item[0].get("left") or 0.0) - left)
            )[1]
        return cells[0][1]
    if fallback:
        if left is None:
            return fallback[0]
        index = int(left // 180.0)
        return fallback[max(0, min(index, len(fallback) - 1))]
    return None


def parse_timetable(html: str, fallback_days: list[date] | None = None) -> list[Tag]:
    parser = _TimetableParser()
    parser.feed(html)
    parser.close()

    cells: list[tuple[dict, date]] = []
    days: dict[date, Tag] = {}
    for cell in parser.cells:
        day = _parse_date(cell.get("date") or "")
        if day is None:
            continue
        cells.append((cell, day))
        days.setdefault(day, Tag(datum=day, wochentag=wochentag(day)))

    for event in parser.events:
        veranstaltung = _parse_tooltip(event.get("lines") or [])
        if veranstaltung is None:
            continue
        day = _day_for_left(event.get("left"), cells, fallback_days)
        if day is None:
            continue
        days.setdefault(day, Tag(datum=day, wochentag=wochentag(day)))
        days[day].veranstaltungen.append(veranstaltung)

    for tag in days.values():
        tag.veranstaltungen.sort(
            key=lambda item: (item.start, item.ende, item.titel)
        )
    return [
        tag
        for tag in sorted(days.values(), key=lambda item: item.datum)
        if tag.veranstaltungen
    ]
