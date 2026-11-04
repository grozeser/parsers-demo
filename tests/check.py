"""Проверка выгрузок: python -m tests.check (после запуска парсеров).

Сверяет количество и типы данных, а если есть LibreOffice — пересчитывает формулы сводок и ищет ошибки.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook

OUT = Path(__file__).resolve().parent.parent / "output"


def rows(name: str) -> list[tuple]:
    return list(load_workbook(OUT / f"{name}.xlsx").worksheets[0].iter_rows(min_row=2, values_only=True))


books = rows("books")
assert len(books) == 1000, len(books)
assert len({b[5] for b in books}) == 1000, "дубли по UPC"
assert all(b[0] and 5 < b[2] < 100 and 1 <= b[3] <= 5 and b[4] >= 0 for b in books)
assert any("é" in b[0] or "’" in b[0] for b in books), "кодировка названий"

quotes = rows("quotes")
assert len(quotes) == 100 and all(q[0] and q[1] for q in quotes)
assert not any(q[0].startswith("“") for q in quotes), "кавычки не срезаны"

oscars = rows("oscars")
assert len(oscars) == 87
assert {o[0] for o in oscars} == set(range(2010, 2016))
assert all(sum(o[4] == "Да" for o in oscars if o[0] == y) == 1 for y in range(2010, 2016)), "по одному лучшему фильму в год"

hockey = rows("hockey")
assert len(hockey) == 582 and len({h[0] for h in hockey}) == 35
assert all(h[8] == h[6] - h[7] for h in hockey), "разница = забито − пропущено"

soffice = shutil.which("soffice") or next((p for p in [r"C:\Program Files\LibreOffice\program\soffice.exe"] if Path(p).exists()), None)
if soffice:
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("books", "quotes", "oscars", "hockey"):
            subprocess.run([soffice, "--headless", "--convert-to", "xlsx", "--outdir", tmp, str(OUT / f"{name}.xlsx")],
                           check=True, capture_output=True)
            sheet = load_workbook(Path(tmp) / f"{name}.xlsx", data_only=True)["Сводка"]
            values = [c.value for row in sheet.iter_rows(min_row=2) for c in row]
            assert values and not any(isinstance(v, str) and v.startswith("#") for v in values), f"{name}: ошибка в формулах"
            assert all(v is not None for v in values), f"{name}: пустые формулы"
    print("формулы сводок пересчитаны LibreOffice: ошибок нет")
else:
    print("LibreOffice не найден: формулы не пересчитаны")
print("ok: все выгрузки прошли проверку")
