FROM python:3.10-slim

LABEL org.opencontainers.image.title="Ghana child-nutrition SAE"
LABEL org.opencontainers.image.description="Reproducible Bayesian small-area estimation + ML pipeline for childhood stunting, anaemia, IYCF inadequacy and diarrhoea across the 261 districts of Ghana (GDHS 2022 + PHC 2021)."
LABEL org.opencontainers.image.authors="Valentine Golden Ghanem <valentineghanem@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies for geospatial libraries + Node.js for the manuscript builder.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gdal-bin \
        libgdal-dev \
        libproj-dev \
        proj-data \
        proj-bin \
        libgeos-dev \
        curl \
        ca-certificates \
        gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# docx (Node) is small; installed locally for the manuscript builder.
COPY scripts/build_manuscript.js ./scripts/build_manuscript.js
RUN npm install docx@8.5.0

COPY . .

# Default: print the project README.
CMD ["bash", "-lc", "echo 'Run: bash run_all.sh    (or invoke individual scripts; see README §7)'"]
