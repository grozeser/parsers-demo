"""Каталог интернет-магазина books.toscrape.com: все страницы и карточки товаров → Excel со сводкой по категориям.

python -m parsers.books
"""
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.common import Timer, get, save_xlsx, session

START = "https://books.toscrape.com/catalogue/page-1.html"
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def product_links(s) -> list[str]:
    links, url = [], START
    while url:  # идём по «next», пока страница есть: число страниц заранее не знаем
        soup = BeautifulSoup(get(s, url).text, "html.parser")
        links += [urljoin(url, a["href"]) for a in soup.select("article.product_pod h3 a")]
        nxt = soup.select_one("li.next a")
        url = urljoin(url, nxt["href"]) if nxt else None
    return links


def product(s, url: str) -> list:
    soup = BeautifulSoup(get(s, url).content, "html.parser")
    info = {th.text: td.text for th, td in zip(soup.select("table th"), soup.select("table td"))}
    stock = re.search(r"\d+", info.get("Availability", ""))
    rating = soup.select_one("p.star-rating")["class"][1]
    return [
        soup.h1.text.strip(),
        soup.select("ul.breadcrumb li a")[2].text.strip(),
        float(soup.select_one("p.price_color").text.lstrip("£Â")),
        RATING[rating],
        int(stock.group()) if stock else 0,
        info["UPC"],
        url,
    ]


def main() -> list[list]:
    s = session()
    with Timer() as t:
        links = product_links(s)
        with ThreadPoolExecutor(8) as pool:  # 8 потоков: быстро, но без нагрузки на сайт
            rows = list(pool.map(lambda u: product(s, u), links))
    rows.sort(key=lambda r: r[0])
    cats = sorted({r[1] for r in rows})
    n = len(rows) + 1
    summary = [["Категория", "Товаров", "Средняя цена, £", "Средний рейтинг", "На складе, шт"]] + [
        [c, f"=COUNTIF(Каталог!B2:B{n},A{i})", f"=ROUND(AVERAGEIF(Каталог!B2:B{n},A{i},Каталог!C2:C{n}),2)",
         f"=ROUND(AVERAGEIF(Каталог!B2:B{n},A{i},Каталог!D2:D{n}),1)", f"=SUMIF(Каталог!B2:B{n},A{i},Каталог!E2:E{n})"]
        for i, c in enumerate(cats, start=2)
    ]
    save_xlsx(
        "books", "Каталог",
        [("Название", 46, None), ("Категория", 18, None), ("Цена, £", 10, "0.00"), ("Рейтинг", 9, "0"),
         ("В наличии, шт", 12, "0"), ("Артикул (UPC)", 20, None), ("Ссылка", 40, None)],
        rows, summary, {"seconds": t.seconds, "pages": len(links) // 20, "categories": len(cats)},
    )
    print(f"books: {len(rows)} товаров, {len(cats)} категорий за {t.seconds} с")
    return rows


if __name__ == "__main__":
    main()
