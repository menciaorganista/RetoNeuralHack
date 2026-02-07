from pathlib import Path
import json
import cv2

from src.metrics.counts import count_by_class
from src.metrics.occupancy import occupancy_ratio
from src.metrics.density import density_per_megapixel
from src.config import ANALYSIS_DIR

def main(json_path: Path, image_path: Path) -> None:
    analysis = json.loads(json_path.read_text(encoding="utf-8"))
    detections = analysis.get("detections", [])
    print("JSON leído:", json_path)
    print("Num detections:", len(analysis.get("detections", [])))
    print("ANALYSIS_DIR:", ANALYSIS_DIR)

    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]

    metrics = {
        "count_by_class_id": count_by_class(detections),
        "occupancy_ratio": occupancy_ratio(detections, w, h),
        "density_per_megapixel": density_per_megapixel(len(detections), w, h),
    }

    bundle = {
        "scene_id": image_path.stem,
        "image_path": str(image_path),
        "image_width": w,
        "image_height": h,
        "detections": analysis,
        "metrics": metrics,
    }

    out = ANALYSIS_DIR / f"{image_path.stem}_bundle.json"
    print("Guardando bundle en:", out)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"Bundle guardado en: {out}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--image", required=True)
    args = p.parse_args()

    main(Path(args.json), Path(args.image))
