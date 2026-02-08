# src/blockchain/register.py
from __future__ import annotations

from typing import Any

from src.blockchain.hashing import hash_bundle
from src.blockchain.bsv_client import register_on_chain


def register_evidence(bundle: dict[str, Any]) -> dict[str, Any]:
    """
    Always works:
    - computes hash + timestamp (local evidence)
    - tries on-chain (optional). Never crashes.
    Returns:
      {
        "evidence": {...},
        "chain": {...}
      }
    """
    hb = hash_bundle(bundle)

    evidence_record: dict[str, Any] = {
        "analysis_hash": hb["sha256"],
        "timestamp_utc": hb["timestamp_utc"],
        "scene_id": bundle.get("scene_id", "unknown"),
        "model_version": bundle.get("model_version", "MyE_v1"),
    }

    # Optional: attempt on-chain registration
    chain = register_on_chain(evidence_record)

    return {
        "evidence": evidence_record,
        "chain": chain,
    }
