from pathlib import Path
import json
import cv2
from ultralytics import YOLO

from src.vision.infer import run_inference, save_outputs
from src.vision.typology import crop_with_padding, classify_typology_crop
from src.pipeline.run_metrics import main as run_metrics_main
from src.pipeline.add_evidence import main as add_evidence_main
from src.metrics.impact import DEFAULT_WEIGHTS, count_by_typology, impact_score, congestion_index
from src.config import RUNS_DIR, ANALYSIS_DIR

def analyze_scene(
    image_path: Path,
    detector_model_path: Path,
    typology_model_path: Path,
    weights: dict | None = None,
    conf_det: float = 0.25,
    conf_type: float = 0.25,
) -> dict:
    """
    Ejecuta: deteccion (MyE) => tipologia (COCO sobre recortes) => metricas => evidencia.
    Devuelve el bundle final como dict.
    """
    weights = weights or DEFAULT_WEIGHTS

    # 1) Deteccion con vuestro modelo
    analysis = run_inference(image_path, detector_model_path, conf_threshold=conf_det)

    # 2) Tipologia por recorte
    img = cv2.imread(str(image_path))
    type_model = YOLO(str(typology_model_path))

    for det in analysis["detections"]:
        crop = crop_with_padding(img, det["bbox_xyxy"], pad=0.20)
        typ, typ_conf = classify_typology_crop(type_model, crop, conf_threshold=conf_type)
        det["typology"] = typ
        det["typology_confidence"] = typ_conf

    # 3) Guardar outputs visuales + json detecciones
    save_outputs(image_path, analysis)
    det_json_path = ANALYSIS_DIR / f"{image_path.stem}.json"

    # 4) Metricas base (conteo/densidad/ocupacion)
    run_metrics_main(det_json_path, image_path)
    bundle_path = ANALYSIS_DIR / f"{image_path.stem}_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    # 5) Metricas avanzadas (tipologia + pesos)
    dets = bundle["detections"]["detections"]
    typ_counts = count_by_typology(dets)
    score = impact_score(dets, weights)
    cong = congestion_index(bundle["metrics"]["density_per_megapixel"], bundle["metrics"]["occupancy_ratio"])

    bundle["metrics"]["count_by_typology"] = typ_counts
    bundle["metrics"]["impact_score"] = score
    bundle["metrics"]["congestion_index"] = cong
    bundle["metrics"]["impact_weights"] = weights

    # Guardar bundle actualizado
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # 6) Evidencia
    add_evidence_main(bundle_path)
    evidence_path = ANALYSIS_DIR / f"{image_path.stem}_bundle_evidence.json"
    bundle_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    return bundle_evidence
