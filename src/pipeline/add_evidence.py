from pathlib import Path
import json

from src.evidence.hashing import hash_bundle
from src.config import ANALYSIS_DIR

def main(bundle_path: Path) -> None:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    evidence = hash_bundle(bundle)
    bundle["evidence"] = evidence

    out = ANALYSIS_DIR / f"{bundle_path.stem}_evidence.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print("EVIDENCE SHA256:", evidence["sha256"])
    print("EVIDENCE TIMESTAMP:", evidence["timestamp_utc"])
    print("Guardado en:", out)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True)
    args = p.parse_args()

    main(Path(args.bundle))
