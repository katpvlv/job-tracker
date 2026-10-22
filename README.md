# Job Tracker

Скрипт для автоматического отслеживания вакансий на карьерных страницах компаний. Раз в день проходит по списку сайтов, фильтрует вакансии по ключевым словам и показывает результат в локальном HTML-дашборде прямо в браузере.

![dashboard preview](https://i.imgur.com/placeholder.png)

## Возможности

- Отслеживание любого количества карьерных страниц
- Фильтрация по ключевым словам
- Новые вакансии помечаются как **NEW**
- Фильтры по компании, типу роли, поиск по тексту
- Работает полностью локально, без серверов и регистраций

## Быстрый старт

**1. Установи зависимости**
```bash
pip install requests beautifulsoup4
```

**2. Добавь свои компании в `scraper.py`**

Открой файл и найди раздел `SOURCES`. Для каждой компании выбери подходящий парсер:

```python
SOURCES = [
    # Сайты на платформе Greenhouse:
    ("Company A", lambda: parse_greenhouse("Company A", "https://job-boards.greenhouse.io/companya")),

    # Сайты на платформе Teamtailor:
    ("Company B", lambda: parse_teamtailor("Company B", "https://companyb.teamtailor.com/jobs")),

    # Обычные карьерные страницы:
    ("Company C", lambda: parse_generic("Company C", "https://companyc.com/careers")),
]
```

**3. Настрой ключевые слова**

```python
KEYWORDS = [
    "Data Analyst",
    "Product Manager",
    # добавь свои...
]
```

**4. Запусти**
```bash
python scraper.py
```

Откроется файл `dashboard_out.html` — открой его в браузере.

## Как понять какой парсер использовать

| Платформа | Признак | Парсер |
|-----------|---------|--------|
| Greenhouse | URL содержит `greenhouse.io` | `parse_greenhouse` |
| Teamtailor | URL содержит `teamtailor.com` | `parse_teamtailor` |
| Всё остальное | Обычный сайт компании | `parse_generic` |

> `parse_generic` работает для большинства статических карьерных страниц. Если вакансии не находятся — скорее всего сайт загружает их через JavaScript (React/Vue), и нужен [Playwright](https://playwright.dev/python/).

## Автозапуск раз в день

**Mac / Linux** — добавь в cron (`crontab -e`):
```
0 9 * * * cd /путь/к/папке && python scraper.py
```

**Windows** — через Планировщик задач (Task Scheduler):
1. Создай новую задачу
2. Триггер: ежедневно в нужное время
3. Действие: программа `python`, аргументы `scraper.py`, рабочая папка — путь к проекту

## Структура проекта

```
job-tracker/
  scraper.py        — парсер (настраивается здесь)
  dashboard.html    — шаблон дашборда
  dashboard_out.html — результат (создаётся автоматически, не коммитить)
  jobs.json         — данные (создаётся автоматически, не коммитить)
```

## Стек

- Python 3.10+
- [requests](https://pypi.org/project/requests/)
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
