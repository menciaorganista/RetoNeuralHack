from pathlib import Path
import json
import cv2
from ultralytics import YOLO

from src.config import RUNS_DIR, ANALYSIS_DIR


def run_inference(
    image_path: Path,
    model_path: Path,
    conf_threshold: float = 0.25
) -> dict:
    """
    Ejecuta inferencia YOLO sobre una imagen y devuelve las detecciones.
    """

    # Cargar modelo
    model = YOLO(str(model_path))

    # Inferencia
    results = model.predict(
        source=str(image_path),
        conf=conf_threshold,
        save=False
    )

    detections = []

    r = results[0]
    boxes = r.boxes

    if boxes is not None:
        for b in boxes:
            cls_id = int(b.cls.item())
            conf = float(b.conf.item())
            x1, y1, x2, y2 = map(float, b.xyxy[0])
            class_name = model.names[cls_id]

            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "confidence": conf,
                "bbox_xyxy": [x1, y1, x2, y2]
            })


    return {
        "image": image_path.name,
        "num_detections": len(detections),
        "detections": detections
    }


def save_outputs(image_path: Path, analysis: dict):
    """
    Guarda imagen con bounding boxes y JSON de análisis.
    """

    # Cargar imagen
    img = cv2.imread(str(image_path))

    for det in analysis["detections"]:
        x1, y1, x2, y2 = map(int, det["bbox_xyxy"])
        conf = det["confidence"]

        label = f"{det['class_name']} {conf:.2f}"

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)


        cv2.putText(
            img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )


    # Guardar imagen
    out_img = RUNS_DIR / image_path.name
    cv2.imwrite(str(out_img), img)

    # Guardar JSON
    out_json = ANALYSIS_DIR / f"{image_path.stem}.json"
    with open(out_json, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Imagen guardada en: {out_img}")
    print(f"JSON guardado en: {out_json}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Ruta a la imagen")
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Ruta al modelo YOLO"
    )

    args = parser.parse_args()

    image_path = Path(args.image)
    model_path = Path(args.model)

    analysis = run_inference(image_path, model_path)
    save_outputs(image_path, analysis)
