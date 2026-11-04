"""Данные, которые страница подгружает AJAX-ом (scrapethissite.com, «Oscar Winning Films»).

В HTML таблица пустая, но в DevTools видно запрос ?ajax=true&year=… с готовым JSON — берём его напрямую,
это быстрее и надёжнее, чем рендерить страницу в браузере.

python -m parsers.oscars
"""
from bs4 import BeautifulSoup

from parsers.common import Timer, get, save_xlsx, session

PAGE = "https://www.scrapethissite.com/pages/ajax-javascript/"


def main() -> list[list]:
    s = session()
    with Timer() as t:
        years = [int(a["id"]) for a in BeautifulSoup(get(s, PAGE).text, "html.parser").select("a.year-link")]
        rows = []
        for year in sorted(years, reverse=True):
            for film in get(s, PAGE, params={"ajax": "true", "year": year}).json():
                rows.append([year, film["title"].strip(), film["awards"], film["nominations"],
                             "Да" if film.get("best_picture") else "Нет"])
    n = len(rows) + 1
    summary = [["Год", "Фильмов", "Наград", "Номинаций", "Лучший фильм"]] + [
        [y, f"=COUNTIF(Фильмы!A2:A{n},A{i})", f"=SUMIF(Фильмы!A2:A{n},A{i},Фильмы!C2:C{n})",
         f"=SUMIF(Фильмы!A2:A{n},A{i},Фильмы!D2:D{n})",
         next(r[1] for r in rows if r[0] == y and r[4] == "Да")]
        for i, y in enumerate(sorted(years, reverse=True), start=2)
    ]
    save_xlsx(
        "oscars", "Фильмы",
        [("Год", 8, "0"), ("Фильм", 44, None), ("Наград", 10, "0"), ("Номинаций", 12, "0"), ("Лучший фильм", 14, None)],
        rows, summary, {"seconds": t.seconds, "requests": len(years) + 1, "years": f"{min(years)}–{max(years)}"},
    )
    print(f"oscars: {len(rows)} фильмов за {min(years)}–{max(years)}, {len(years) + 1} запросов за {t.seconds} с")
    return rows


if __name__ == "__main__":
    main()
