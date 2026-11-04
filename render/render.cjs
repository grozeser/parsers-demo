// Картинки парсеров для портфолио по реальным выгрузкам: node render/render.cjs → docs/<имя>.png
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { createRequire } = require('module');
const { chromium } = createRequire('E:/Портфолио/omega-hakaton/e2e/')('@playwright/test');

const root = path.join(__dirname, '..');
const preview = (name) => JSON.parse(fs.readFileSync(path.join(root, 'output', `${name}.preview.json`), 'utf8'));
const num = (n) => n.toLocaleString('ru-RU');

function cards() {
    const b = preview('books'), q = preview('quotes'), o = preview('oscars'), h = preview('hockey');
    return {
        books: [{ tag: 'Парсер · Python', title: 'Каталог <em>магазина</em> в Excel', sub: 'Все страницы и карточки товаров books.toscrape.com',
            file: 'books.xlsx', stats: [[num(b.total), 'товаров'], [b.categories, 'категорий'], [`${b.seconds} с`, 'на всё']],
            features: ['Обход пагинации и карточек', 'Цена, рейтинг, остаток, артикул', 'Сводка по категориям формулами', '8 потоков и повторы при сбоях'],
            cols: [[0, 330], [1, 120], [2, 80, 'money'], [3, 80], [4, 110]] }, b],
        quotes: [{ tag: 'Парсер · Playwright', title: 'Сайт <em>на JavaScript</em>', sub: 'quotes.toscrape.com/js: контент рисует скрипт, обычный запрос пустой',
            file: 'quotes.xlsx', stats: [[q.total, 'цитат'], [q.pages, 'страниц'], [q.authors, 'авторов']],
            features: ['Настоящий браузер вместо запросов', 'Переход по страницам кнопкой', 'Теги и автор в отдельных колонках', 'Топ авторов на листе «Сводка»'],
            cols: [[0, 440], [1, 150], [2, 230]] }, q],
        oscars: [{ tag: 'Парсер · API', title: 'Нашёл <em>скрытое API</em>', sub: 'scrapethissite.com: таблица грузится AJAX-ом, данные берём из JSON',
            file: 'oscars.xlsx', stats: [[o.total, 'фильмов'], [o.requests, 'запросов'], [`${o.seconds} с`, 'на всё']],
            features: ['Запрос найден через DevTools', 'Без браузера: быстро и стабильно', 'Награды и номинации числами', 'Сводка по годам с лучшим фильмом'],
            cols: [[0, 70], [1, 400], [2, 100], [3, 120], [4, 130]] }, o],
        hockey: [{ tag: 'Парсер · Python', title: 'Таблица <em>с&nbsp;пагинацией</em>', sub: 'scrapethissite.com: 6 страниц статистики хоккейных команд',
            file: 'hockey.xlsx', stats: [[h.total, 'строк'], [h.pages, 'страниц'], [h.teams, 'команд']],
            features: ['Обход всех страниц таблицы', 'Числа — числами, пропуски — пустыми', 'Проверка, что разница шайб сходится', 'Итоги по командам на листе «Сводка»'],
            cols: [[0, 210], [1, 64], [2, 86], [3, 100], [5, 90, 'pct'], [6, 80], [7, 100], [8, 84, 'diff']] }, h],
        'client-search': [{ tag: 'Парсер · Десктоп', title: 'Поиск клиентов <em>с&nbsp;карт</em>', sub: 'Моё приложение: заведения с карт с контактами и CRM-таблицей',
            file: 'Поиск клиентов', stats: [['Excel', 'выгрузка'], ['SQLite', 'база'], ['0 ₽', 'без API']],
            features: ['Сбор по рубрикам и городу', 'Телефоны, сайты и мессенджеры', 'Статусы и заметки по клиентам', 'Выгрузка выбранных в Excel'],
            image: pathToFileURL('E:/Портфолио/client-search/docs/screenshots/table.png').href }, null],
    };
}

(async () => {
    const browser = await chromium.launch({ channel: 'msedge' });
    const page = await browser.newPage({ viewport: { width: 1320, height: 880 }, deviceScaleFactor: 1.5 });
    await page.goto(pathToFileURL(path.join(__dirname, 'card.html')).href);
    fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
    for (const [name, [meta, data]] of Object.entries(cards())) {
        await page.evaluate(([m, d]) => window.renderCard(m, d), [meta, data]);
        await page.evaluate(() => document.fonts.ready);
        await page.waitForLoadState('networkidle');
        await page.locator('#card').screenshot({ path: path.join(root, 'docs', `${name}.png`) });
    }
    await browser.close();
    console.log('ok', Object.keys(cards()).length);
})().catch((e) => { console.error(e); process.exit(1); });
