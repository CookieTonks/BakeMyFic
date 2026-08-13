# Railway's Root Directory for this service is "backend", so the build
# context is this folder itself (not the repo root) — every COPY below is
# relative to backend/. main.py reads its default cover from ./img/Portada Bunny.png.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
