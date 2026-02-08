from pathlib import Path
from ultralytics import YOLO
import cv2

# Mapeo COCO (YOLOv8 COCO) a tipologias que nos interesan
# COCO ids: 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck
COCO_TO_TYPOLOGY = {
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

def classify_typology_crop(model: YOLO, crop_bgr, conf_threshold: float = 0.25) -> tuple[str, float]:
    """
    Devuelve (tipology, confidence). Si no reconoce, ('unknown', 0.0).
    """
    results = model.predict(crop_bgr, conf=conf_threshold, verbose=False)
    r = results[0]
    if r.boxes is None or len(r.boxes) == 0:
        return "unknown", 0.0

    # Elegimos la prediccion con mayor confianza
    best = None
    best_conf = -1.0
    for b in r.boxes:
        cls_id = int(b.cls.item())
        conf = float(b.conf.item())
        if conf > best_conf:
            best_conf = conf
            best = cls_id

    typ = COCO_TO_TYPOLOGY.get(best, "unknown")
    return typ, best_conf

def crop_with_padding(img_bgr, bbox_xyxy, pad: float = 0.15):
    h, w = img_bgr.shape[:2]
    x1, y1, x2, y2 = bbox_xyxy

    bw = x2 - x1
    bh = y2 - y1

    x1p = max(0, int(x1 - pad * bw))
    y1p = max(0, int(y1 - pad * bh))
    x2p = min(w, int(x2 + pad * bw))
    y2p = min(h, int(y2 + pad * bh))

    return img_bgr[y1p:y2p, x1p:x2p]
