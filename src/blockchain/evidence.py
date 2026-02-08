from datetime import datetime, timezone
from typing import Any

from hashing import hash_bundle


def build_evidence_record(bundle: dict[str, Any], scene_id: str) -> dict[str, Any]:
    h = hash_bundle(bundle)
    return {
        "analysis_hash": h["sha256"],
        "scene_id": scene_id,
        "created_utc": h["timestamp_utc"],
        # Keep full payload in local ledger; on-chain only analysis_hash + scene_id + version/prefix
        "bundle": bundle,
        # Optional: store canonical used to hash for reproducibility/debug
        "bundle_canonical": h["canonical_json"],
    }
