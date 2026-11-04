"""Сайт, который рисует контент JavaScript-ом (quotes.toscrape.com/js): обычный запрос вернёт пустую страницу,
поэтому открываем её в браузере через Playwright и листаем «Next».

python -m parsers.quotes_js
"""
from playwright.sync_api import sync_playwright

from parsers.common import Timer, save_xlsx

START = "https://quotes.toscrape.com/js/"


def main() -> list[list]:
    rows = []
    with Timer() as t, sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")  # установленный Edge, браузеры Playwright скачивать не нужно
        page = browser.new_page()
        page.goto(START)
        pages = 0
        while True:
            page.wait_for_selector(".quote")
            pages += 1
            for q in page.locator(".quote").all():
                rows.append([
                    q.locator(".text").inner_text().strip("“”"),
                    q.locator(".author").inner_text(),
                    ", ".join(q.locator(".tag").all_inner_texts()),
                    page.url,
                ])
            nxt = page.locator("li.next a")
            if not nxt.count():
                break
            nxt.click()
            page.wait_for_load_state()
        browser.close()
    authors = sorted({r[1] for r in rows}, key=lambda a: -sum(r[1] == a for r in rows))
    n = len(rows) + 1
    summary = [["Автор", "Цитат"]] + [[a, f"=COUNTIF(Цитаты!B2:B{n},A{i})"] for i, a in enumerate(authors, start=2)]
    save_xlsx(
        "quotes", "Цитаты",
        [("Цитата", 80, None), ("Автор", 22, None), ("Теги", 34, None), ("Страница", 36, None)],
        rows, summary, {"seconds": t.seconds, "pages": pages, "authors": len(authors)},
    )
    print(f"quotes: {len(rows)} цитат с {pages} страниц, {len(authors)} авторов за {t.seconds} с")
    return rows


if __name__ == "__main__":
    main()
