# flowMD — image autonome (modèles inclus : fonctionne 100 % hors ligne)
FROM python:3.12-slim

# Tesseract + données ara/fra/eng : moteur recommandé pour les documents
# mélangeant arabe et français.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-ara \
        tesseract-ocr-fra \
        tesseract-ocr-eng \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch CPU d'abord (évite les roues CUDA de plusieurs Go)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

# Modèles cuits dans l'image : ~2 Go, mais docker compose up fonctionne
# ensuite sans aucun accès réseau.
ENV FLOWMD_DATA_DIR=/app/data
RUN flowmd setup

ENV FLOWMD_HOST=0.0.0.0
EXPOSE 8000
CMD ["flowmd", "serve"]
