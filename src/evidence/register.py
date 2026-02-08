from src.evidence.hashing import hash_bundle
from src.evidence.bsv_client import register_on_chain

def register_evidence(bundle: dict) -> dict:
    evidence = hash_bundle(bundle)

    evidence_record = {
        "analysis_hash": evidence["sha256"],
        "timestamp_utc": evidence["timestamp_utc"],
        "scene_id": bundle.get("scene_id", "unknown"),
        "model_version": bundle.get("model_version", "MyE_v1"),
    }

    result = register_on_chain(evidence_record)
    return result
