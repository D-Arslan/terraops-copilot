# TerraOps Copilot — agent + Streamlit UI.
#
# Why this image is big (~3 GB): the RAG embedder needs torch, and the drift tool runs
# TerraOps' own drift_report.py (mounted read-only at /terraops), which needs torch,
# torchvision, pandas and Evidently. A slimmer image would need TerraOps to expose a
# drift endpoint - a documented debt on that side, not fixed here on purpose.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/cache/hf TOKENIZERS_PARALLELISM=false

WORKDIR /app

# CPU-only torch first (the default index would pull CUDA wheels, +2 GB for nothing).
COPY requirements-docker.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.10.0 torchvision==0.25.0 \
 && pip install -r requirements-docker.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY corpus ./corpus
COPY ui ./ui
COPY docker/entrypoint.sh /entrypoint.sh
RUN pip install --no-deps -e . && chmod +x /entrypoint.sh

EXPOSE 8502
ENTRYPOINT ["/entrypoint.sh"]
