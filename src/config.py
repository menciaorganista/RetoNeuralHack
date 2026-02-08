from pathlib import Path

# Raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas de datos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Resultados
REPORTS_DIR = BASE_DIR / "reports"
RUNS_DIR = REPORTS_DIR / "runs"
ANALYSIS_DIR = REPORTS_DIR / "analysis_json"

# Configs
CONFIGS_DIR = BASE_DIR / "configs"

# Crear carpetas si no existen
for path in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    RUNS_DIR,
    ANALYSIS_DIR
]:
    path.mkdir(parents=True, exist_ok=True)


# ============================================================
# BLOCKCHAIN / BSV
# ============================================================
BSV_NETWORK = "main"
WOC_BASE = "https://api.whatsonchain.com/v1/bsv/main"

BSV_PRIVATE_KEY = "L4DArgykDjNHg1UvvSiEB1qK7RkcayJQ9ZypuDeKGWhvMEmZsmHt"  # empty = local-only mode

ARC_URL = "https://arc.gorillapool.io"


LEDGER_PATH = DATA_DIR / "evidence_ledger.jsonl"
