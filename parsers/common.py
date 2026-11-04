"""Общее для парсеров: HTTP-сессия с повторами и выгрузка в оформленный Excel."""
import json
import time
from pathlib import Path

import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OUT = Path(__file__).resolve().parent.parent / "output"
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")


def session() -> requests.Session:
    """Сессия с повторами на 429/5xx: сайт моргнул — парсер не падает."""
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (parsers-demo; practice project)"
    retry = Retry(total=4, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
    return s


def get(s: requests.Session, url: str, **kw) -> requests.Response:
    r = s.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r


def save_xlsx(name: str, title: str, columns: list[tuple[str, int, str | None]], rows: list[list],
              summary: list[list] | None = None, meta: dict | None = None) -> Path:
    """columns: (заголовок, ширина, числовой формат). summary — строки листа «Сводка», можно с формулами.

    Рядом пишет <name>.preview.json: первые строки и цифры для картинки в портфолио.
    """
    OUT.mkdir(exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = title
    ws.append([c[0] for c in columns])
    for row in rows:
        ws.append(row)
    for i, (_, width, fmt) in enumerate(columns, start=1):
        letter = get_column_letter(i)
        ws.column_dimensions[letter].width = width
        ws[f"{letter}1"].font = Font(bold=True, color="FFFFFF")
        ws[f"{letter}1"].fill = HEADER_FILL
        ws[f"{letter}1"].alignment = Alignment(vertical="center", wrap_text=True)
        if fmt:
            for cell in ws[letter][1:]:
                cell.number_format = fmt
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    if summary:
        sm = wb.create_sheet("Сводка")
        for row in summary:
            sm.append(row)
        for cell in sm[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = HEADER_FILL
        for i, width in enumerate([34, 16, 16, 16, 16], start=1):
            sm.column_dimensions[get_column_letter(i)].width = width
    path = OUT / f"{name}.xlsx"
    wb.save(path)
    preview = {"title": title, "columns": [c[0] for c in columns], "rows": rows[:16], "total": len(rows), **(meta or {})}
    (OUT / f"{name}.preview.json").write_text(json.dumps(preview, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = round(time.perf_counter() - self.start)
