from app.utils.config import ensure_directories, CLIP_MODEL_NAME, RECOMMENDER_WEIGHTS
from app.utils.logger import get_logger
from app.utils.helpers import sigmoid, safe_divide, normalize_scores, compute_eta_from_distance

ensure_directories()

logger = get_logger("test")
logger.info("Logger is working")

print(CLIP_MODEL_NAME)
print(RECOMMENDER_WEIGHTS)
print(sigmoid(2.0))
print(safe_divide(10, 2))
print(normalize_scores([10, 20, 30]))
print(compute_eta_from_distance(8.5))