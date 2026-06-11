import io
import os
import re
import tempfile

from ebooklib import epub

from scraper import WorkData

KINDLE_CSS = """
body {
    font-family: Georgia, serif;
    font-size: 1em;
    line-height: 1.7;
    margin: 0 5%;
    color: #1a1a1a;
}
h1 {
    font-size: 1.4em;
    font-weight: bold;
    margin: 1.5em 0 0.8em;
    text-align: center;
}
p {
    margin: 0 0 0.8em;
    text-indent: 1.2em;
}
p:first-of-type { text-indent: 0; }
hr {
    border: none;
    border-top: 1px solid #aaa;
    margin: 1.5em auto;
    width: 40%;
}
"""


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip() or "fic"


def build_epub(work: WorkData, cover_bytes: bytes | None) -> bytes:
    book = epub.EpubBook()
    book.set_title(work.title)
    book.set_language(work.language or "en")
    book.add_author(work.author)

    if work.summary:
        book.add_metadata("DC", "description", work.summary)

    if cover_bytes:
        ext = "png" if cover_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "jpg"
        book.set_cover(f"cover.{ext}", cover_bytes)

    style = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=KINDLE_CSS,
    )
    book.add_item(style)

    epub_chapters = []
    toc_links = []

    for i, ch in enumerate(work.chapters):
        title = ch.title or f"Capítulo {i + 1}"
        fname = f"chap_{i + 1:03d}.xhtml"
        epub_ch = epub.EpubHtml(title=title, file_name=fname, lang=work.language or "en")
        epub_ch.content = f"<h1>{title}</h1>\n{ch.html}"
        epub_ch.add_item(style)
        book.add_item(epub_ch)
        epub_chapters.append(epub_ch)
        toc_links.append(epub.Link(fname, title, f"chap_{i + 1}"))

    book.toc = toc_links
    book.spine = ["nav"] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        tmp = f.name
    try:
        epub.write_epub(tmp, book)
        with open(tmp, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp)


def epub_filename(title: str) -> str:
    return _safe_filename(title) + ".epub"
