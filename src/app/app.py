
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image

# Project root (kept as in your previous app)
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.vision.infer import run_inference, save_outputs  # noqa: E402
from src.pipeline.run_metrics import main as run_metrics_main  # noqa: E402
from src.pipeline.add_evidence import main as add_evidence_main  # noqa: E402
from src.config import RUNS_DIR, ANALYSIS_DIR  # noqa: E402


# -----------------------------
# Page + styles
# -----------------------------
st.set_page_config(page_title="MyE Traffic UAV", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; padding-bottom: 1.1rem; }
      header, footer { visibility: hidden; }
      [data-testid="stToolbar"] { visibility: hidden; height: 0px; }

      .title-wrap { text-align: center; margin-bottom: 0.2rem; }
      .subtitle-wrap { text-align: center; margin-top: 0.0rem; margin-bottom: 0.85rem; font-size: 1.05rem; color: #3b3b3b; }

      .card {
        background: #ffffff;
        border: 1px solid #ececec;
        border-radius: 16px;
        padding: 14px 14px;
        box-shadow: 0 1px 10px rgba(0,0,0,0.04);
        margin-bottom: 10px;
      }

      .thermo-title { font-weight: 800; font-size: 1.1rem; margin-bottom: 10px; }
      .thermo-wrap {
        background: #ffffff;
        border: 1px solid #ececec;
        border-radius: 18px;
        padding: 14px 14px 16px 14px;
        box-shadow: 0 1px 10px rgba(0,0,0,0.04);
      }
      .thermo-bar {
        width: 64px;
        height: 200px;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #e7e7e7;
        background: #f7f7f7;
        display: flex;
        flex-direction: column;
      }
      .thermo-seg {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.9rem;
        color: rgba(0,0,0,0.55);
      }
      .seg-low { background: rgba(46, 204, 113, 0.22); }
      .seg-med { background: rgba(241, 196, 15, 0.22); }
      .seg-high { background: rgba(231, 76, 60, 0.22); }
      .active-low { background: rgba(46, 204, 113, 0.75); color: #0b2a18; }
      .active-med { background: rgba(241, 196, 15, 0.80); color: #3a2f00; }
      .active-high { background: rgba(231, 76, 60, 0.80); color: #2b0a07; }

      .thermo-row { display: flex; gap: 14px; align-items: center; }
      .thermo-text { line-height: 1.25; }
      .thermo-text .big { font-weight: 900; font-size: 1.2rem; margin-bottom: 4px; }
      .thermo-text .small { font-size: 0.95rem; color: #3b3b3b; }

      .stButton > button {
        border-radius: 14px;
        padding: 0.75rem 1.0rem;
        font-weight: 800;
        font-size: 1.05rem;
      }

      .tight-metrics [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #ececec;
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 1px 10px rgba(0,0,0,0.04);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Thermometer helper
# -----------------------------
def render_thermometer(label: str, density_percent: float) -> None:
    label_u = (label or "").upper().strip()
    active_low = "active-low" if label_u == "BAJA" else ""
    active_med = "active-med" if label_u == "MEDIA" else ""
    active_high = "active-high" if label_u == "ALTA" else ""

    st.markdown(
        f"""
        <div class="thermo-wrap">
          <div class="thermo-title">Densidad</div>
          <div class="thermo-row">
            <div class="thermo-bar" aria-label="traffic-density-thermometer">
              <div class="thermo-seg seg-high {active_high}">ALTA</div>
              <div class="thermo-seg seg-med {active_med}">MEDIA</div>
              <div class="thermo-seg seg-low {active_low}">BAJA</div>
            </div>
            <div class="thermo-text">
              <div class="big">Densidad: {label_u}</div>
              <div class="small">{density_percent:.1f}%</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Robust parsing helpers (bundle/detections formats may vary)
# -----------------------------
def _safe_get(d: Dict[str, Any], keys: Tuple[str, ...], default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _density_label_from_percent(p: float) -> str:
    if p < 5.0:
        return "BAJA"
    if p < 12.0:
        return "MEDIA"
    return "ALTA"


def _extract_counts_from_bundle(bundle: Dict[str, Any]) -> Dict[str, int]:
    # Preferred: what your run_metrics writes
    counts = _safe_get(bundle, ("metrics", "count_by_class_id"), None)
    if isinstance(counts, dict):
        return {str(k): int(v) for k, v in counts.items()}

    # Compatibility
    counts = _safe_get(bundle, ("metrics", "counts_by_class"), None)
    if isinstance(counts, dict):
        return {str(k): int(v) for k, v in counts.items()}

    counts = _safe_get(bundle, ("metrics", "counts"), None)
    if isinstance(counts, dict):
        return {str(k): int(v) for k, v in counts.items()}

    # Fallback: count from detections list
    dets = _safe_get(bundle, ("detections", "detections"), None)
    if not isinstance(dets, list):
        dets = _safe_get(bundle, ("detections",), None)

    out: Dict[str, int] = {}
    if isinstance(dets, list):
        for det in dets:
            if not isinstance(det, dict):
                continue

            cls = det.get("class_name")
            if cls is None:
                cls = det.get("class_id")

            if cls is None:
                continue

            cls_s = str(cls)
            out[cls_s] = out.get(cls_s, 0) + 1

    return out



def _extract_metrics(bundle: Dict[str, Any]) -> Dict[str, Any]:
    m = _safe_get(bundle, ("metrics",), {})
    if not isinstance(m, dict):
        m = {}

    # Total density: prefer occupancy_ratio (0..1)
    total_density = m.get("occupancy_ratio")
    if total_density is None:
        total_density = m.get("total_density") or m.get("density_total") or m.get("density") or m.get("traffic_density")

    # Heavy density (may be missing -> 0)
    heavy_density = m.get("heavy_density")
    if heavy_density is None:
        heavy_density = m.get("density_heavy") or m.get("heavy_vehicles_density") or 0.0

    # Totals: prefer explicit values, else take from detections.num_detections
    total_vehicles = m.get("total_vehicles")
    if total_vehicles is None:
        total_vehicles = m.get("vehicle_count") or m.get("num_vehicles")

    if total_vehicles is None:
        total_vehicles = _safe_get(bundle, ("detections", "num_detections"), None)

    heavy_vehicles = m.get("heavy_vehicles")
    if heavy_vehicles is None:
        heavy_vehicles = m.get("heavy_count") or m.get("num_heavy")

    # If still missing, infer from counts
    counts = _extract_counts_from_bundle(bundle)

    if total_vehicles is None:
        total_vehicles = int(sum(counts.values()))

    if heavy_vehicles is None:
        heavy_vehicles = int(counts.get("bus", 0) + counts.get("truck", 0) + counts.get("camion", 0))

    def _to_percent(x: Any) -> float:
        try:
            v = float(x)
        except Exception:
            return 0.0
        return v * 100.0 if 0.0 <= v <= 1.0 else v

    # Normalize to percent for UI
    total_density_pct = _to_percent(total_density)
    heavy_density_pct = _to_percent(heavy_density)

    total_label = m.get("total_label") or m.get("density_label") or _density_label_from_percent(total_density_pct)
    heavy_label = m.get("heavy_label") or m.get("heavy_density_label") or _density_label_from_percent(heavy_density_pct)

    return {
        "counts": counts,
        "total_vehicles": int(total_vehicles) if total_vehicles is not None else 0,
        "heavy_vehicles": int(heavy_vehicles) if heavy_vehicles is not None else 0,
        "total_density_pct": float(total_density_pct),
        "heavy_density_pct": float(heavy_density_pct),
        "total_label": str(total_label),
        "heavy_label": str(heavy_label),
    }



# -----------------------------
# State
# -----------------------------
def init_state() -> None:
    if "img_hash" not in st.session_state:
        st.session_state.img_hash = None
    if "uploaded_name" not in st.session_state:
        st.session_state.uploaded_name = None
    if "display_image_path" not in st.session_state:
        st.session_state.display_image_path = None
    if "metrics" not in st.session_state:
        st.session_state.metrics = None
    if "evidence" not in st.session_state:
        st.session_state.evidence = None


init_state()

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="title-wrap"><h1>MyE - Sistema Inteligente de Analisis de Trafico (UAV)</h1></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle-wrap">Sube una imagen y pulsa Analizar para obtener metricas de trafico.</div>',
    unsafe_allow_html=True,
)

model_path = Path("weights/MyE_best.pt").resolve()
conf = 0.45


uploaded = st.file_uploader("Imagen", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded is None:
    st.markdown(
        """
        <div class="card" style="max-width: 900px; margin: 0 auto;">
          <div style="font-weight:900; font-size:1.1rem; margin-bottom:6px;">Instrucciones</div>
          <div style="color:#3b3b3b;">
            Inserta una imagen arriba. Al pulsar Analizar, la imagen se reemplaza por la anotada y debajo aparecen las metricas.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

file_bytes = uploaded.getvalue()
img_hash = hashlib.sha256(file_bytes).hexdigest()

# Reset state if new image
if st.session_state.img_hash != img_hash:
    st.session_state.img_hash = img_hash
    st.session_state.uploaded_name = uploaded.name
    st.session_state.metrics = None
    st.session_state.evidence = None

    # Save uploaded bytes to RUNS_DIR with original filename (nice outputs)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    img_for_outputs = RUNS_DIR / uploaded.name
    img_for_outputs.write_bytes(file_bytes)

    # Show original until analyzed
    st.session_state.display_image_path = str(img_for_outputs)

# Top: single (smaller) image + analyze button (no duplication)
top_left, top_right = st.columns([5, 2], vertical_alignment="bottom")
with top_left:
    st.image(st.session_state.display_image_path, width=760)

with top_right:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    analyze = st.button("Analizar", use_container_width=True)

if analyze and st.session_state.metrics is None:
    with st.spinner("Analizando..."):
        # We reuse the RUNS_DIR image file (the one we just saved) as input
        img_for_outputs = RUNS_DIR / st.session_state.uploaded_name

        # Some pipelines expect a real file path, keep a temp file for inference if needed
        suffix = Path(st.session_state.uploaded_name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        # 1) Inference (project script)
        analysis = run_inference(tmp_path, Path(model_path), conf_threshold=conf)

        # 2) Save outputs (project script)
        save_outputs(img_for_outputs, analysis)

        # Convention from your previous app
        det_json_path = ANALYSIS_DIR / f"{Path(st.session_state.uploaded_name).stem}.json"

        # 3) Metrics (project script)
        run_metrics_main(det_json_path, img_for_outputs)

        bundle_path = ANALYSIS_DIR / f"{Path(st.session_state.uploaded_name).stem}_bundle.json"

        # 4) Evidence (project script)
        add_evidence_main(bundle_path)

        evidence_path = ANALYSIS_DIR / f"{Path(st.session_state.uploaded_name).stem}_bundle_evidence.json"

        # Image with detections (your pipeline saves it in RUNS_DIR with the same name)
        out_img = RUNS_DIR / st.session_state.uploaded_name
        st.session_state.display_image_path = str(out_img)

        # Load results
        bundle = json.loads(bundle_path.read_text(encoding="utf-8")) if bundle_path.exists() else {}
        evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else {}

        st.session_state.metrics = _extract_metrics(bundle)
        st.session_state.evidence = evidence.get("evidence") or evidence

    st.rerun()

# Metrics below the image (only after analyzing)
if st.session_state.metrics is not None:
    metrics = st.session_state.metrics
    counts = metrics["counts"]

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([2, 5], gap="large")

    with left:
        render_thermometer(metrics["total_label"], metrics["total_density_pct"])

        st.markdown('<div class="tight-metrics">', unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            st.metric("Total vehiculos", f"{metrics['total_vehicles']}")
        with b:
            st.metric("Densidad total", f"{metrics['total_density_pct']:.1f}%")

        c, d = st.columns(2)
        with c:
            st.metric("Pesados", f"{metrics['heavy_vehicles']}")
        with d:
            st.metric("Densidad pesados", f"{metrics['heavy_density_pct']:.1f}%")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="card">
              <div style="font-weight:900; font-size:1.05rem; margin-bottom:6px;">
                Pesados: {metrics['heavy_label']}
              </div>
              <div style="color:#3b3b3b;">Bus + camion en escena</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Evidence (kept compact)
        ev = st.session_state.evidence or {}
        sha = ev.get("sha256")
        ts = ev.get("timestamp_utc")
        if sha or ts:
            st.markdown(
                """
                <div class="card">
                  <div style="font-weight:900; font-size:1.05rem; margin-bottom:6px;">Evidencia verificable</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if sha:
                st.code(str(sha))
            if ts:
                st.write("Timestamp UTC:", str(ts))

    with right:
        records = [{"categoria": str(k), "conteo": int(v)} for k, v in (counts or {}).items()]
        df = pd.DataFrame(records, columns=["categoria", "conteo"])

        if df.empty:
            st.markdown(
                """
                <div class="card">
                <div style="font-weight:900; font-size:1.05rem; margin-bottom:6px;">Conteo por categoria</div>
                <div style="color:#3b3b3b;">No hay datos de categorias disponibles en el bundle.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            df = df.sort_values("conteo", ascending=False)

            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("categoria:N", sort="-y", title="Categoria"),
                    y=alt.Y("conteo:Q", title="Conteo"),
                    tooltip=["categoria:N", "conteo:Q"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)
