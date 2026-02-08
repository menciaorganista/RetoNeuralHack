# src/app/ui_helpers.py
from __future__ import annotations

def extract_detections(bundle: dict) -> list[dict]:
    d = bundle.get("detections", {})
    if isinstance(d, dict) and "detections" in d and isinstance(d["detections"], list):
        return d["detections"]
    if "detections" in bundle and isinstance(bundle["detections"], list):
        return bundle["detections"]
    return []

def typology_color_bgr(typ: str) -> tuple[int, int, int]:
    palette = {
        "car": (60, 220, 120),
        "bus": (0, 190, 255),
        "truck": (80, 80, 255),
        "motorcycle": (220, 90, 220),
        "bicycle": (255, 160, 60),
        "unknown": (180, 180, 180),
    }
    return palette.get(typ, (0, 255, 0))
