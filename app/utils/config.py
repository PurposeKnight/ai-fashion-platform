from pathlib import Path


# -----------------------------
# Base paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
SCHEMA_DIR = DATA_DIR / "schemas"

ARTIFACTS_DIR = BASE_DIR / "artifacts"
EMBEDDINGS_DIR = ARTIFACTS_DIR / "embeddings"
MODELS_DIR = ARTIFACTS_DIR / "models"
FAISS_DIR = ARTIFACTS_DIR / "faiss"

LOGS_DIR = BASE_DIR / "logs"


# -----------------------------
# File paths
# -----------------------------
CATALOGUE_FILE = PROCESSED_DATA_DIR / "catalogue.json"
WAREHOUSES_FILE = PROCESSED_DATA_DIR / "warehouses.json"
INVENTORY_FILE = PROCESSED_DATA_DIR / "inventory.json"
TRANSFER_MATRIX_FILE = PROCESSED_DATA_DIR / "transfer_matrix.json"
DEMAND_HISTORY_FILE = PROCESSED_DATA_DIR / "demand_history.json"

TEXT_EMBEDDINGS_FILE = EMBEDDINGS_DIR / "catalog_text_embeddings.npy"
IMAGE_EMBEDDINGS_FILE = EMBEDDINGS_DIR / "catalog_image_embeddings.npy"
PRODUCT_INDEX_FILE = EMBEDDINGS_DIR / "product_index.json"
FAISS_INDEX_FILE = FAISS_DIR / "catalog.index"

POINT_FORECAST_MODEL_FILE = MODELS_DIR / "forecast_model.pkl"
LOWER_QUANTILE_MODEL_FILE = MODELS_DIR / "forecast_q10.pkl"
UPPER_QUANTILE_MODEL_FILE = MODELS_DIR / "forecast_q90.pkl"


# -----------------------------
# Model names
# -----------------------------
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


# -----------------------------
# API defaults
# -----------------------------
DEFAULT_TOP_K = 5
DEFAULT_RETRIEVAL_TOP_N = 100
FORECAST_HORIZON_HOURS = 6
DEFAULT_NUM_WAREHOUSES = 10
DEFAULT_CATALOGUE_SIZE = 500
DEFAULT_SYNTHETIC_DAYS = 30


# -----------------------------
# Recommender weights
# -----------------------------
RECOMMENDER_WEIGHTS = {
    "retrieval_score": 0.50,
    "category_match": 0.10,
    "occasion_match": 0.08,
    "color_match": 0.08,
    "style_match": 0.08,
    "inventory_score": 0.08,
    "price_fit_score": 0.05,
    "popularity_score": 0.05,
    "return_rate_penalty": 0.06,
}


# -----------------------------
# Forecasting config
# -----------------------------
FORECAST_CONFIG = {
    "horizon_hours": FORECAST_HORIZON_HOURS,
    "default_frequency": "H",
    "min_history_hours": 24,
    "quantiles": [0.10, 0.90],
}


# -----------------------------
# Risk thresholds
# -----------------------------
RISK_THRESHOLDS = {
    "low": 0.30,
    "medium": 0.70,
    "high": 1.00,
}


# -----------------------------
# Inventory / transfer config
# -----------------------------
INVENTORY_CONFIG = {
    "default_safety_stock_ratio": 0.15,
    "default_reorder_threshold_ratio": 0.25,
    "max_transfer_eta_mins": 60,
    "default_transfer_buffer_units": 3,
    "max_service_radius_km": 5,
}


TRANSFER_ETA_THRESHOLD_MINS = 60


# -----------------------------
# Artifact paths in grouped form
# -----------------------------
ARTIFACT_PATHS = {
    "text_embeddings": str(TEXT_EMBEDDINGS_FILE),
    "image_embeddings": str(IMAGE_EMBEDDINGS_FILE),
    "product_index": str(PRODUCT_INDEX_FILE),
    "faiss_index": str(FAISS_INDEX_FILE),
    "forecast_model": str(POINT_FORECAST_MODEL_FILE),
    "forecast_q10_model": str(LOWER_QUANTILE_MODEL_FILE),
    "forecast_q90_model": str(UPPER_QUANTILE_MODEL_FILE),
}


# -----------------------------
# Directory bootstrap
# -----------------------------
def ensure_directories() -> None:
    for path in [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        SYNTHETIC_DATA_DIR,
        SCHEMA_DIR,
        EMBEDDINGS_DIR,
        MODELS_DIR,
        FAISS_DIR,
        LOGS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)