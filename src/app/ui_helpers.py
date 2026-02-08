from __future__ import annotations

def extract_detections(bundle: dict) -> list[dict]:
    # Tu pipeline guarda detecciones dentro de bundle["detections"]["detections"]
    d = bundle.get("detections", {})
    if isinstance(d, dict) and "detections" in d and isinstance(d["detections"], list):
        return d["detections"]
    # Fallback si alguna vez guardais en otro formato
    if "detections" in bundle and isinstance(bundle["detections"], list):
        return bundle["detections"]
    return []

def typology_color_bgr(typ: str) -> tuple[int, int, int]:
    # Colores limpios por tipologia (BGR para cv2)
    palette = {
        "car": (0, 200, 0),
        "bus": (255, 120, 0),
        "truck": (0, 0, 255),
        "motorcycle": (200, 0, 200),
        "bicycle": (200, 200, 0),
        "unknown": (180, 180, 180),
    }
    return palette.get(typ, (0, 255, 0))
