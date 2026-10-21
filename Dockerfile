FROM python:3.12-slim-bookworm
# OCR、繁體中文語言包、PDF 轉圖及中文字型一併封裝，主機不用另裝。
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-chi-tra poppler-utils fonts-dejavu-core fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --uid 10001 -m worker && mkdir -p output && chown -R worker:worker /app
USER worker
ENV OCR_LANG=eng PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=3)"
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8080"]
