import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


def extract_work_id(url: str) -> int:
    match = re.search(r"/works/(\d+)", url)
    if not match:
        raise ValueError("URL de AO3 no válida. Debe ser archiveofourown.org/works/XXXXXX")
    return int(match.group(1))


@dataclass
class Chapter:
    title: str
    html: str


@dataclass
class WorkData:
    title: str
    author: str
    language: str
    summary: str
    chapters: list[Chapter]


def _fetch_html(work_id: int) -> str:
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0 ao3-epub-tool"

    url = f"https://archiveofourown.org/works/{work_id}?view_full_work=true"
    r = sess.get(url, timeout=90)

    if "This work could have adult content" in r.text:
        r = sess.get(url + "&view_adult=true", timeout=90)

    if r.status_code == 404:
        raise LookupError(f"Obra {work_id} no encontrada en AO3.")
    if "This work is only available to registered users" in r.text:
        raise PermissionError("Esta obra requiere iniciar sesión en AO3.")
    if r.status_code != 200:
        raise RuntimeError(f"AO3 respondió con HTTP {r.status_code}")

    return r.text


def _text(tag) -> str:
    return tag.get_text(strip=True) if tag else ""


def _parse_work(html: str) -> WorkData:
    soup = BeautifulSoup(html, "html.parser")

    title = _text(soup.select_one("h2.title.heading"))
    author = _text(soup.select_one("h3.byline a[rel='author']"))
    if not author:
        author = _text(soup.select_one("h3.byline"))

    lang_dd = soup.select_one("dd.language")
    language = lang_dd.get_text(strip=True) if lang_dd else "en"

    summary_bq = soup.select_one("div.summary blockquote")
    summary = str(summary_bq) if summary_bq else ""

    chapters: list[Chapter] = []
    chapter_divs = soup.select("div#chapters div.chapter")
    if chapter_divs:
        for div in chapter_divs:
            title_tag = div.select_one("h3.title")
            ch_title = _text(title_tag) if title_tag else ""
            content = div.select_one("div.userstuff")
            if not content:
                continue
            for landmark in content.select("h3.landmark"):
                landmark.decompose()
            chapters.append(Chapter(title=ch_title, html=str(content)))
    else:
        content = soup.select_one("div#chapters div.userstuff")
        if content:
            for landmark in content.select("h3.landmark"):
                landmark.decompose()
            chapters.append(Chapter(title=title, html=str(content)))

    if not chapters:
        raise RuntimeError("No se encontró contenido de capítulos en la obra.")

    return WorkData(
        title=title or "Sin título",
        author=author or "Desconocido",
        language=language,
        summary=summary,
        chapters=chapters,
    )


def fetch_info(url: str) -> dict:
    work_id = extract_work_id(url)
    html = _fetch_html(work_id)
    work = _parse_work(html)
    return {
        "title": work.title,
        "author": work.author,
    }


def fetch_work(url: str) -> WorkData:
    work_id = extract_work_id(url)
    html = _fetch_html(work_id)
    return _parse_work(html)
