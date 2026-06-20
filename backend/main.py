import asyncio
import io
import pathlib

from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from scraper import fetch_info, fetch_work
from epub_gen import build_epub, epub_filename

DEFAULT_COVER = pathlib.Path(__file__).parent.parent / "img" / "Portada Bunny.png"

app = FastAPI(title="Bake My Fic! API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your domain in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/info")
async def info(url: str = Form(...)):
    """Returns title, author and chapter count for a given AO3 URL."""
    try:
        data = await asyncio.to_thread(fetch_info, url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar con AO3: {e}")
    return data


@app.post("/convert")
async def convert(
    url: str = Form(...),
    cover: UploadFile = File(None),
):
    """Fetches the work, builds an EPUB and streams it back."""
    cover_bytes = None
    if cover and cover.filename:
        cover_bytes = await cover.read()
    elif DEFAULT_COVER.exists():
        cover_bytes = DEFAULT_COVER.read_bytes()

    try:
        work = await asyncio.to_thread(fetch_work, url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar con AO3: {e}")

    try:
        epub_bytes = await asyncio.to_thread(build_epub, work, cover_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el EPUB: {e}")

    filename = epub_filename(work.title)
    return StreamingResponse(
        io.BytesIO(epub_bytes),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
