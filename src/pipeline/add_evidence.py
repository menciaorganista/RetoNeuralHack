from pathlib import Path
import json

from src.blockchain.hashing import hash_bundle
from src.blockchain.adapter import get_blockchain_adapter
from src.config import ANALYSIS_DIR


def main(bundle_path: Path) -> None:
    # 1. Load final analysis bundle
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    # 2. Compute evidence hash (THIS is what goes on-chain)
    evidence = hash_bundle(bundle)
    bundle["evidence"] = evidence

    # 3. Register evidence (local ledger or BSV on-chain)
    adapter = get_blockchain_adapter()

    evidence_record = {
        "analysis_hash": evidence["sha256"],
        "scene_id": bundle.get("scene_id", bundle_path.stem),
        "timestamp_utc": evidence["timestamp_utc"],
        # optional but useful for audit/debug
        "analysis_payload": bundle,
    }

    result = adapter.register(evidence_record)

    # 4. Save enriched bundle to disk
    out = ANALYSIS_DIR / f"{bundle_path.stem}_evidence.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # 5. Log
    print("EVIDENCE SHA256:", evidence["sha256"])
    print("EVIDENCE TIMESTAMP:", evidence["timestamp_utc"])
    print("BLOCKCHAIN STATUS:", result["status"])
    if "tx_id" in result:
        print("TX ID:", result["tx_id"])
    if "explorer_url" in result:
        print("EXPLORER:", result["explorer_url"])
    print("Guardado en:", out)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True)
    args = p.parse_args()

    main(Path(args.bundle))
