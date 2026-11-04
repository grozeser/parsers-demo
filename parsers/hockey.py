"""Таблица с поиском и пагинацией (scrapethissite.com, «Hockey Teams»): обходим все страницы,
приводим числа к числам и считаем сводку по командам.

python -m parsers.hockey
"""
from bs4 import BeautifulSoup

from parsers.common import Timer, get, save_xlsx, session

URL = "https://www.scrapethissite.com/pages/forms/"
FIELDS = ["name", "year", "wins", "losses", "ot-losses", "pct", "gf", "ga", "diff"]


def num(text: str):
    text = text.strip()
    if not text:
        return None  # в ранних сезонах нет поражений в овертайме
    return float(text) if "." in text else int(text)


def main() -> list[list]:
    s = session()
    rows, page = [], 1
    with Timer() as t:
        while True:
            soup = BeautifulSoup(get(s, URL, params={"page_num": page, "per_page": 100}).text, "html.parser")
            teams = soup.select("tr.team")
            if not teams:
                break
            for tr in teams:
                cells = [tr.select_one(f"td.{f}").text for f in FIELDS]
                rows.append([cells[0].strip()] + [num(c) for c in cells[1:]])
            page += 1
    names = sorted({r[0] for r in rows})
    n = len(rows) + 1
    summary = [["Команда", "Сезонов", "Побед", "Поражений", "Разница шайб"]] + [
        [name, f"=COUNTIF(Сезоны!A2:A{n},A{i})", f"=SUMIF(Сезоны!A2:A{n},A{i},Сезоны!C2:C{n})",
         f"=SUMIF(Сезоны!A2:A{n},A{i},Сезоны!D2:D{n})", f"=SUMIF(Сезоны!A2:A{n},A{i},Сезоны!I2:I{n})"]
        for i, name in enumerate(names, start=2)
    ]
    save_xlsx(
        "hockey", "Сезоны",
        [("Команда", 26, None), ("Год", 8, "0"), ("Победы", 9, "0"), ("Поражения", 11, "0"), ("Пораж. в ОТ", 11, "0"),
         ("% побед", 9, "0.000"), ("Забито", 9, "0"), ("Пропущено", 11, "0"), ("Разница", 9, "+0;-0;0")],
        rows, summary, {"seconds": t.seconds, "pages": page - 1, "teams": len(names)},
    )
    print(f"hockey: {len(rows)} сезонов, {len(names)} команд, {page - 1} страниц за {t.seconds} с")
    return rows


if __name__ == "__main__":
    main()
