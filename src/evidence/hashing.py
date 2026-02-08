import json
import hashlib
from datetime import datetime, timezone

def canonical_json(obj) -> str:
    # JSON estable: siempre el mismo orden, sin espacios raros
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def hash_bundle(bundle: dict) -> dict:
    canon = canonical_json(bundle)
    digest = sha256_hex(canon)

    return {
        "sha256": digest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
