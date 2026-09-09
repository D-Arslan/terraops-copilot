#!/bin/sh
# 1. wait for the TerraOps API (it publishes its port ~40 s before it listens);
# 2. build the vector store on first boot (persisted in the rag-store volume);
# 3. serve the UI.
set -e

echo "[copilot] waiting for TerraOps API at ${TERRAOPS_API_URL} ..."
python - <<'PY'
import os, sys
sys.path.insert(0, "/app/src")
from terraops_copilot.client.terraops_api import TerraOpsClient
h = TerraOpsClient().wait_ready(seconds=300)
print(f"[copilot] API ready: model_loaded={h.get('model_loaded')} version={h.get('model_version')}")
PY

if [ ! -f "${RAG_STORE_PATH}/chroma.sqlite3" ]; then
  echo "[copilot] vector store empty -> ingesting corpus"
  python -m terraops_copilot.rag.ingest --store "${RAG_STORE_PATH}"
fi

exec streamlit run /app/ui/app.py --server.port 8502 --server.address 0.0.0.0 \
     --server.headless true --browser.gatherUsageStats false
