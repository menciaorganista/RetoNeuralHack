from __future__ import annotations

import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

import config


logger = logging.getLogger(__name__)

# Protocol prefix for OP_RETURN data
APP_PREFIX = "TRAFFIC_EVIDENCE"
APP_VERSION = "v1.0"


# ======================================================================
# INTEGRITY (HASHING) - CASE (A)
# ======================================================================

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
    timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """
    Canonical payload BEFORE hashing.
    timestamp_utc is included INSIDE payload (case A).
    """
    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()

    payload: dict[str, Any] = {
        "scene_id": scene_id,
        "dataset_id": dataset_id,
        "timestamp_utc": ts,
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
    Evidence record consumed by adapter.register().

    adapter expects:
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

    # Useful for local ledger: audit/debug and later verification
    if store_payload_locally:
        record["analysis_payload"] = analysis_payload
        record["analysis_payload_canonical"] = canonical_json(analysis_payload)

    return record


def verify_integrity(analysis_payload: dict[str, Any], expected_hash: str) -> bool:
    """Recompute hash and compare."""
    return compute_hash(analysis_payload) == expected_hash


# ======================================================================
# ADAPTER INTERFACES
# ======================================================================

class BlockchainAdapter(ABC):
    """Abstract interface for evidence registration."""

    @abstractmethod
    def register(self, evidence_record: dict[str, Any]) -> dict[str, Any]:
        """Register evidence. Returns {tx_id, status, ...}."""
        ...

    @abstractmethod
    def verify(self, analysis_hash: str) -> dict[str, Any] | None:
        """Look up registered evidence by analysis_hash."""
        ...

    @abstractmethod
    def list_records(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent evidence records."""
        ...


# ======================================================================
# LOCAL JSONL LEDGER (always active, also used as cache for BSV)
# ======================================================================

class LocalLedgerAdapter(BlockchainAdapter):
    """Local JSONL file ledger for demo/offline mode and as BSV cache."""

    def __init__(self, ledger_path: str | Path | None = None):
        self.ledger_path = Path(ledger_path) if ledger_path else Path(config.LEDGER_PATH)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def register(self, evidence_record: dict[str, Any]) -> dict[str, Any]:
        evidence_id = str(uuid.uuid4())
        entry = {
            "evidence_id": evidence_id,
            **evidence_record,
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n")

        logger.info(
            "[LOCAL] Registered %s -> %s",
            str(evidence_record.get("analysis_hash", ""))[:16],
            evidence_id[:8],
        )
        return {
            "evidence_id": evidence_id,
            "tx_id": f"local_{evidence_id[:8]}",
            "status": "registered",
        }

    def verify(self, analysis_hash: str) -> dict[str, Any] | None:
        if not self.ledger_path.exists():
            return None

        text = self.ledger_path.read_text(encoding="utf-8").strip()
        if not text:
            return None

        for line in text.splitlines():
            record = json.loads(line)
            if record.get("analysis_hash") == analysis_hash:
                return record
        return None

    def list_records(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        text = self.ledger_path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        lines = text.splitlines()
        records = [json.loads(line) for line in lines[-limit:]]
        return list(reversed(records))

    def _update_record_txid(self, analysis_hash: str, txid: str) -> None:
        """Update a local record with the on-chain txid."""
        if not self.ledger_path.exists():
            return

        text = self.ledger_path.read_text(encoding="utf-8").strip()
        if not text:
            return

        lines = text.splitlines()
        updated_lines: list[str] = []
        for line in lines:
            record = json.loads(line)
            if record.get("analysis_hash") == analysis_hash:
                record["tx_id"] = txid
            updated_lines.append(json.dumps(record, sort_keys=True, ensure_ascii=True))

        self.ledger_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


# ======================================================================
# BSV ON-CHAIN ADAPTER (bsv-sdk + ARC broadcaster)
# ======================================================================

class BSVAdapter(BlockchainAdapter):
    """
    Real BSV blockchain adapter using bsv-sdk for OP_RETURN transactions.

    Uses ARC for broadcasting and WhatsOnChain API for UTXO lookups and tx verification.
    All records are also saved to local ledger for fast lookups.
    """

    def __init__(self):
        self.private_key_wif = getattr(config, "BSV_PRIVATE_KEY", "")
        self.network = getattr(config, "BSV_NETWORK", "testnet")  # "main" or "testnet"
        self.arc_url = getattr(config, "ARC_URL", "")
        self.woc_base = getattr(config, "WOC_BASE", "")
        self._local = LocalLedgerAdapter()  # always keep local copy

        self._key = None
        self._address = None

        if not self.private_key_wif:
            logger.warning("BSV_PRIVATE_KEY not set - BSVAdapter in local-only mode")
        else:
            self._init_key()

    def _init_key(self) -> None:
        """Initialize bsv-sdk PrivateKey from WIF."""
        try:
            from bsv import PrivateKey
            self._key = PrivateKey(self.private_key_wif)
            self._address = self._key.address()
            logger.info("[BSV] Initialized key, address: %s", self._address)
        except Exception as e:
            logger.error("[BSV] Failed to init PrivateKey: %s", e)
            self._key = None
            self._address = None

    @property
    def is_configured(self) -> bool:
        return self._key is not None and bool(self.woc_base) and bool(self.arc_url)

    @property
    def address(self) -> str | None:
        return self._address

    # ---- UTXO fetching via WhatsOnChain ----

    def _fetch_utxos(self) -> list[dict[str, Any]]:
        """Fetch unspent outputs for our address from WhatsOnChain."""
        if not self._address:
            return []
        url = f"{self.woc_base}/address/{self._address}/unspent"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        utxos = resp.json()
        logger.info("[BSV] Found %d UTXOs for %s", len(utxos), self._address)
        return utxos

    def _fetch_raw_tx(self, txid: str) -> str:
        """Fetch raw transaction hex from WhatsOnChain."""
        url = f"{self.woc_base}/tx/{txid}/hex"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text.strip()

    # ---- Transaction building ----

    def _build_op_return_tx(self, analysis_hash: str, scene_id: str) -> Any:
        """Build a signed OP_RETURN transaction using bsv-sdk."""
        from bsv import (
            Transaction, TransactionInput, TransactionOutput,
            P2PKH, OpReturn,
        )

        if not self._address or not self._key:
            raise RuntimeError("BSV key/address not initialized")

        utxos = self._fetch_utxos()
        if not utxos:
            raise RuntimeError(
                f"No UTXOs available for address {self._address}. "
                "Fund the address to broadcast on-chain."
            )

        # Pick UTXO with max value (simple selection)
        utxo = max(utxos, key=lambda u: u.get("value", 0))
        source_txid = utxo["tx_hash"]
        source_vout = utxo["tx_pos"]
        source_satoshis = utxo["value"]

        logger.info(
            "[BSV] Using UTXO %s:%d (%d sats)",
            source_txid, source_vout, source_satoshis,
        )

        raw_hex = self._fetch_raw_tx(source_txid)
        source_tx = Transaction.from_hex(raw_hex)

        tx = Transaction()

        tx_input = TransactionInput(
            source_transaction=source_tx,
            source_output_index=source_vout,
            unlocking_script_template=P2PKH().unlock(self._key),
        )
        tx.add_input(tx_input)

        # OP_RETURN data: keep it minimal
        # Format: [APP_PREFIX, analysis_hash, scene_id, APP_VERSION]
        op_return_data = [
            APP_PREFIX,
            analysis_hash,
            scene_id,
            APP_VERSION,
        ]
        data_output = TransactionOutput(
            locking_script=OpReturn().lock(op_return_data),
            satoshis=0,
        )
        tx.add_output(data_output)

        # Change back to our address
        change_output = TransactionOutput(
            locking_script=P2PKH().lock(self._address),
            change=True,
        )
        tx.add_output(change_output)

        # Fee and sign
        tx.fee()
        tx.sign()

        logger.info(
            "[BSV] Built tx %s (%d bytes, fee=%d sats)",
            tx.txid(), tx.byte_length(), tx.get_fee(),
        )
        return tx

    def _broadcast_tx(self, tx: Any) -> str:
        """Broadcast transaction via ARC. Returns txid."""
        from bsv import ARC

        broadcaster = ARC(self.arc_url)
        response = broadcaster.sync_broadcast(tx, timeout=30)

        if getattr(response, "status", "") == "success":
            txid = getattr(response, "txid", "")
            if not txid:
                raise RuntimeError("ARC broadcast success but txid missing")
            logger.info("[BSV] Broadcast success: %s", txid)
            return txid

        desc = getattr(response, "description", None) or getattr(response, "message", None) or "unknown"
        raise RuntimeError(f"ARC broadcast failed: {getattr(response, 'status', 'error')} - {desc}")

    def _explorer_url(self, txid: str) -> str:
        """Build WhatsOnChain explorer URL."""
        if self.network == "testnet":
            return f"https://test.whatsonchain.com/tx/{txid}"
        return f"https://whatsonchain.com/tx/{txid}"

    # ---- Public API ----

    def register(self, evidence_record: dict[str, Any]) -> dict[str, Any]:
        # Always save locally first (fast, resilient)
        local_result = self._local.register(evidence_record)

        if not self.is_configured:
            logger.info("[BSV] Not configured - registered locally only")
            return {**local_result, "status": "local_only"}

        analysis_hash = evidence_record["analysis_hash"]
        scene_id = evidence_record.get("scene_id", "unknown")

        try:
            tx = self._build_op_return_tx(analysis_hash, scene_id)
            txid = self._broadcast_tx(tx)

            # Update local record with real txid
            self._local._update_record_txid(analysis_hash, txid)

            return {
                "tx_id": txid,
                "status": "on_chain",
                "network": self.network,
                "explorer_url": self._explorer_url(txid),
                "evidence_id": local_result.get("evidence_id"),
                "address": self._address,
            }

        except RuntimeError as e:
            logger.warning("[BSV] %s", e)
            return {
                **local_result,
                "status": "local_fallback",
                "warning": str(e),
                "address": self._address,
            }

        except Exception as e:
            logger.error("[BSV] Unexpected error: %s", e, exc_info=True)
            return {
                **local_result,
                "status": "error",
                "error": str(e),
                "address": self._address,
            }

    def verify(self, analysis_hash: str) -> dict[str, Any] | None:
        # Check local ledger first
        record = self._local.verify(analysis_hash)
        if not record:
            return None

        txid = record.get("tx_id", "")
        if txid and isinstance(txid, str) and not txid.startswith("local_"):
            # Verify on-chain via WhatsOnChain
            try:
                resp = requests.get(f"{self.woc_base}/tx/{txid}", timeout=10)
                if resp.status_code == 200:
                    tx_data = resp.json()
                    record["on_chain_verified"] = True
                    record["confirmations"] = tx_data.get("confirmations", 0)
                    record["explorer_url"] = self._explorer_url(txid)

                    hex_resp = requests.get(f"{self.woc_base}/tx/{txid}/hex", timeout=10)
                    record["raw_tx_available"] = hex_resp.status_code == 200
                else:
                    record["on_chain_verified"] = False
            except Exception as e:
                record["on_chain_verified"] = False
                record["verify_error"] = str(e)

        return record

    def list_records(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._local.list_records(limit=limit)


# ======================================================================
# FACTORY
# ======================================================================

def get_blockchain_adapter() -> BlockchainAdapter:
    """Returns BSVAdapter (falls back internally to local ledger)."""
    return BSVAdapter()
