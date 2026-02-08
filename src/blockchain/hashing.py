# src/blockchain/integrity.py
"""
Deterministic hashing for (A): each analysis is unique (timestamp inside hash).

- analysis_payload includes timestamp_utc
- analysis_hash = SHA256(canonical_json(analysis_payload))
- evidence_record is what adapter.register() consumes

Rule:
- To verify, you MUST keep the original analysis_payload (or at least the exact timestamp_utc).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    """
    Deterministic JSON:
    - sort_keys=True for stable ordering
    - separators remove whitespace
    - ensure_ascii=True for cross-platform reproducibility
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(data: dict[str, Any]) -> str:
    """SHA-256 hex of canonical JSON."""
    canon = canonical_json(data)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """SHA-256 hex of file bytes."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def build_analysis_payload(
    scene_id: str,
    dataset_id: str,
    counts: dict[str, int],
    total_vehicles: int,
    density_grid: list[list[int]],
    occupancy_pct: float,
    zone_occupancy: dict[str, float],
    risk_level: str,
    model_version: str,
    is_roundabout: bool = False,
    roundabout_occupancy_pct: float | None = None,
    collision_count: int = 0,
    collisions: list[dict[str, Any]] | None = None,
    geo: dict[str, Any] | None = None,
    # For verification/replay you may pass the exact timestamp_utc you stored
    timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """
    Canonical payload BEFORE hashing.
    Timestamp is included INSIDE payload (case A).
    """
    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()

    payload: dict[str, Any] = {
        "scene_id": scene_id,
        "dataset_id": dataset_id,
        "timestamp_utc": ts,  # included in hash (A)
        "model_version": model_version,
        "counts": counts,
        "total_vehicles": total_vehicles,
        "density_grid": density_grid,
        "occupancy_pct": occupancy_pct,
        "zone_occupancy": zone_occupancy,
        "risk_level": risk_level,
        "is_roundabout": is_roundabout,
        "collision_count": collision_count,
    }

    if roundabout_occupancy_pct is not None:
        payload["roundabout_occupancy_pct"] = roundabout_occupancy_pct
    if collisions:
        payload["collisions"] = collisions
    if geo:
        payload["geo"] = geo

    return payload


def build_evidence_record(
    analysis_payload: dict[str, Any],
    image_hash: str | None = None,
    store_payload_locally: bool = True,
) -> dict[str, Any]:
    """
    Evidence record for adapter.register().

    adapter.py needs:
    - analysis_hash (required)
    - scene_id (optional but recommended)
    """
    analysis_hash = compute_hash(analysis_payload)

    record: dict[str, Any] = {
        "analysis_hash": analysis_hash,
        "scene_id": analysis_payload.get("scene_id", "unknown"),
        "dataset_id": analysis_payload.get("dataset_id", "unknown"),
        "timestamp_utc": analysis_payload.get("timestamp_utc"),
        "model_version": analysis_payload.get("model_version"),
    }

    if image_hash:
        record["image_hash"] = image_hash

    # Useful for your LocalLedgerAdapter audit/debug
    if store_payload_locally:
        record["analysis_payload"] = analysis_payload
        record["analysis_payload_canonical"] = canonical_json(analysis_payload)

    return record


def verify_integrity(analysis_payload: dict[str, Any], expected_hash: str) -> bool:
    """Recompute and compare."""
    return compute_hash(analysis_payload) == expected_hash
