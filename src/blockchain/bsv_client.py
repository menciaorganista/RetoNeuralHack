from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import requests

from src import config

try:
    from bsv import ARC, P2PKH, PrivateKey, Script, Transaction, TransactionInput, TransactionOutput
    _BSV_AVAILABLE = True
except ImportError:
    _BSV_AVAILABLE = False


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _op_return_script(prefix: str, payload: dict[str, Any]):
    data = (prefix + _canonical_json(payload)).encode("utf-8")
    return Script.from_asm(f"OP_FALSE OP_RETURN {data.hex()}")


def _woc_get_json(path: str) -> Any:
    url = f"{config.WOC_BASE.rstrip('/')}/{path.lstrip('/')}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def _woc_get_text(path: str) -> str:
    url = f"{config.WOC_BASE.rstrip('/')}/{path.lstrip('/')}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def _pick_utxo(address: str, min_sats: int = 600) -> dict[str, Any] | None:
    utxos = _woc_get_json(f"address/{address}/unspent")
    if not isinstance(utxos, list) or len(utxos) == 0:
        return None

    ok = [u for u in utxos if int(u.get("value", 0)) >= min_sats]
    if not ok:
        return None

    ok.sort(key=lambda u: int(u.get("value", 0)))
    return ok[0]


async def _broadcast_with_arc(tx: Transaction, arc_url: str, arc_api_key: str | None) -> None:
    if arc_api_key:
        broadcaster = ARC(arc_url, arc_api_key)
    else:
        broadcaster = ARC(arc_url)
    await tx.broadcast(broadcaster)


def register_on_chain(evidence_record: dict[str, Any]) -> dict[str, Any]:
    """
    Register evidence_record on BSV (OP_FALSE OP_RETURN <data>).
    Config comes from src/config.py.
    Returns:
      {"status":"ok","txid":"..."} OR {"status":"failed","error":"..."} OR {"status":"skipped","reason":"..."}
    """
    if not _BSV_AVAILABLE:
        return {"status": "skipped", "reason": "bsv-sdk not installed"}

    wif = (getattr(config, "BSV_PRIVATE_KEY", "") or "").strip()
    if wif == "":
        return {"status": "skipped", "reason": "BSV_PRIVATE_KEY empty (local-only mode)"}

    arc_url = (getattr(config, "ARC_URL", "") or "").strip()
    if arc_url == "":
        return {"status": "failed", "error": "ARC_URL missing in config.py"}

    arc_api_key_cfg = (getattr(config, "ARC_API_KEY", "") or "").strip()
    arc_api_key_env = (os.getenv("ARC_API_KEY", "") or "").strip()
    arc_api_key = arc_api_key_cfg or arc_api_key_env or None

    prefix = (os.getenv("MYE_OPRETURN_PREFIX", "MYE|EVID|v1|") or "MYE|EVID|v1|").strip()

    try:
        priv = PrivateKey(wif)  
        addr = getattr(config, "BSV_ADDRESS", "") or ""
        addr = addr.strip() if isinstance(addr, str) else ""
        if addr == "":
            addr = str(priv.address())

        utxo = _pick_utxo(addr, min_sats=600)
        if utxo is None:
            return {
                "status": "failed",
                "error": f"No UTXO >= 600 sats for address {addr}. Fund this address first."
            }

        src_txid = utxo.get("tx_hash") or utxo.get("tx_hash_big_endian")
        src_vout = int(utxo.get("tx_pos"))
        src_value = int(utxo.get("value", 0))

        if not src_txid:
            return {"status": "failed", "error": "WhatsOnChain UTXO missing tx_hash"}

        source_tx_hex = _woc_get_text(f"tx/{src_txid}/hex").strip()
        source_tx = Transaction.from_hex(source_tx_hex)

        tx_in = TransactionInput(
            source_transaction=source_tx,
            source_txid=source_tx.txid(),
            source_output_index=src_vout,
            unlocking_script_template=P2PKH().unlock(priv),
        )

        opret = _op_return_script(prefix, evidence_record)
        opret_out = TransactionOutput(locking_script=opret, satoshis=0)

        change_out = TransactionOutput(
            locking_script=P2PKH().lock(priv.address()),
            change=True
        )

        tx = Transaction([tx_in], [opret_out, change_out], version=1)
        tx.fee()
        tx.sign()

        asyncio.run(_broadcast_with_arc(tx, arc_url, arc_api_key))

        return {
            "status": "ok",
            "txid": tx.txid(),
            "address": addr,
            "funding_utxo": {"txid": src_txid, "vout": src_vout, "value": src_value},
            "arc_url": arc_url,
        }

    except Exception as ex:
        return {"status": "failed", "error": str(ex)}
