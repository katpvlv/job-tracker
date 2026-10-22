#!/usr/bin/env python3
"""
Job Tracker — парсер вакансий с карьерных страниц
Запускай раз в день: python scraper.py
Результат открывается в dashboard_out.html
"""

import requests
import json
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
#  НАСТРОЙКИ — редактируй этот раздел под себя
# ─────────────────────────────────────────────

KEYWORDS = [
    # Добавь свои ключевые слова для фильтрации вакансий
    "Data Analyst",
    "Product Analyst",
    "Marketing Analyst",
    "BI Analyst",
    "Web Analyst",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────

def keyword_match(title: str) -> bool:
    """Проверяет, содержит ли название вакансии одно из ключевых слов."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in KEYWORDS)


def get_html(url: str) -> BeautifulSoup | None:
    """Загружает страницу и возвращает BeautifulSoup объект."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  ✗ Ошибка загрузки {url}: {e}")
        return None


def make_job(title: str, url: str, company: str, location: str = "") -> dict:
    return {
        "title": title.strip(),
        "url": url,
        "company": company,
        "location": location.strip(),
        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

# ─────────────────────────────────────────────
#  ГОТОВЫЕ ПАРСЕРЫ
#  Каждая функция заточена под конкретную
#  платформу или структуру сайта.
# ─────────────────────────────────────────────

def parse_greenhouse(company_name: str, board_url: str, base_url: str = ""):
    """
    Парсер для сайтов на платформе Greenhouse.
    Примеры URL: job-boards.greenhouse.io/company
                 job-boards.eu.greenhouse.io/company
    """
    jobs = []
    soup = get_html(board_url)
    if not soup:
        return jobs
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if keyword_match(text) and ("/jobs/" in href or "greenhouse.io" in href):
            if not href.startswith("http"):
                href = (base_url or board_url.split("/jobs")[0]) + href
            parent = a.find_parent()
            location = ""
            if parent:
                loc_el = parent.find(class_=re.compile(r"location|city|place", re.I))
                if loc_el:
                    location = loc_el.get_text(strip=True)
            jobs.append(make_job(text, href, company_name, location))
    return jobs


def parse_teamtailor(company_name: str, url: str):
    """
    Парсер для сайтов на платформе Teamtailor.
    Пример URL: company.teamtailor.com/jobs
    """
    jobs = []
    soup = get_html(url)
    if not soup:
        return jobs
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if keyword_match(text) and "/jobs/" in href:
            if not href.startswith("http"):
                base = "/".join(url.split("/")[:3])
                href = base + href
            location = ""
            parent = a.find_parent("li") or a.find_parent("div")
            if parent:
                for span in parent.find_all(["span", "p"]):
                    t = span.get_text(strip=True)
                    if t and t != text and len(t) < 60:
                        location = t
                        break
            jobs.append(make_job(text, href, company_name, location))
    return jobs


def parse_generic(company_name: str, url: str, base_url: str = ""):
    """
    Универсальный парсер — подходит для большинства статических
    карьерных страниц. Ищет все ссылки, фильтрует по ключевым словам.
    """
    jobs = []
    soup = get_html(url)
    if not soup:
        return jobs
    base = base_url or "/".join(url.split("/")[:3])
    seen = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if keyword_match(text) and len(text) > 5 and text not in seen:
            seen.add(text)
            href = a["href"]
            if href.startswith("/"):
                href = base + href
            elif not href.startswith("http"):
                href = url.rstrip("/") + "/" + href
            jobs.append(make_job(text, href, company_name))
    return jobs

# ─────────────────────────────────────────────
#  СПИСОК ИСТОЧНИКОВ
#
#  Добавляй компании сюда в формате:
#  ("Название", lambda: parse_*(аргументы))
#
#  Три варианта парсера:
#  - parse_greenhouse — для сайтов на Greenhouse
#  - parse_teamtailor — для сайтов на Teamtailor
#  - parse_generic    — для всех остальных
# ─────────────────────────────────────────────

SOURCES = [
    # Примеры — замени на свои компании:

    # Greenhouse-платформа:
    # ("Company A", lambda: parse_greenhouse("Company A", "https://job-boards.greenhouse.io/companya")),

    # Teamtailor-платформа:
    # ("Company B", lambda: parse_teamtailor("Company B", "https://companyb.teamtailor.com/jobs")),

    # Обычная карьерная страница:
    # ("Company C", lambda: parse_generic("Company C", "https://companyc.com/careers")),
]

# ─────────────────────────────────────────────
#  ЯДРО — не нужно менять
# ─────────────────────────────────────────────

def load_previous(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"jobs": [], "last_run": None}


def save_data(path: str, data: dict, script_dir: str = ""):
    # Сохраняем jobs.json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Читаем шаблон dashboard.html и создаём dashboard_out.html с вшитыми данными
    base_dir = script_dir or os.path.dirname(os.path.abspath(path))
    template_path = os.path.join(base_dir, "dashboard.html")
    out_path = os.path.join(base_dir, "dashboard_out.html")

    if not os.path.exists(template_path):
        print(f"  ⚠️  dashboard.html не найден в {base_dir}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    json_str = json.dumps(data, ensure_ascii=False)
    injected = f'<script id="job-data">window.__JOBS__ = {json_str};</script>'

    html = re.sub(r'<script id="job-data">.*?</script>\n?', '', html, flags=re.DOTALL)
    html = html.replace('<head>', '<head>\n' + injected, 1)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Готово! Открой dashboard_out.html в браузере ({len(data['jobs'])} вакансий)")


def run():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "jobs.json")
    prev = load_previous(data_path)

    known = {(j["url"], j["title"]) for j in prev.get("jobs", [])}
    new_jobs = []

    print(f"\n🔍 Запуск парсера — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    if not SOURCES:
        print("  ⚠️  Список SOURCES пустой. Добавь компании в scraper.py и запусти снова.")
        return

    for name, parser in SOURCES:
        print(f"  → {name}...", end=" ", flush=True)
        try:
            found = parser()
            unique = list({(j["url"], j["title"]): j for j in found}.values())
            print(f"{len(unique)} совпадений")
            for job in unique:
                if (job["url"], job["title"]) not in known:
                    job["is_new"] = True
                    new_jobs.append(job)
        except Exception as e:
            print(f"ОШИБКА: {e}")

    new_keys = {(j["url"], j["title"]) for j in new_jobs}
    old_jobs = []
    for j in prev.get("jobs", []):
        if (j["url"], j["title"]) not in new_keys:
            j["is_new"] = False
            old_jobs.append(j)
    combined = new_jobs + old_jobs

    data = {
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "new_count": len(new_jobs),
        "total_count": len(combined),
        "jobs": combined,
    }
    save_data(data_path, data, script_dir)

    print(f"\n✅ Готово! Новых вакансий: {len(new_jobs)} / Всего: {len(combined)}\n")


if __name__ == "__main__":
    run()
