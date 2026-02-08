from collections import Counter

DEFAULT_WEIGHTS = {
    "car": 1.0,
    "motorcycle": 0.6,
    "truck": 2.5,
    "bus": 2.0,
    "bicycle": 0.4,
    "unknown": 1.0,
}

def count_by_typology(detections: list[dict]) -> dict:
    types = [d.get("typology", "unknown") for d in detections]
    return dict(Counter(types))

def impact_score(detections: list[dict], weights: dict) -> float:
    total = 0.0
    for d in detections:
        t = d.get("typology", "unknown")
        total += float(weights.get(t, weights.get("unknown", 1.0)))
    return total

def congestion_index(density_per_megapixel: float, occupancy_ratio: float) -> float:
    # Simple, explicable: mezcla de densidad y ocupacion
    return 0.7 * float(density_per_megapixel) + 0.3 * float(occupancy_ratio) * 100.0
