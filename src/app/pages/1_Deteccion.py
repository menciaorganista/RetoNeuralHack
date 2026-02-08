# src/app/pages/1_Deteccion.py
from pathlib import Path
import tempfile
import time

import streamlit as st
import cv2

from src.pipeline.analyze import analyze_scene
from src.app.state import save_last
from src.app.ui_helpers import extract_detections, typology_color_bgr

st.markdown("""
<div class="mye-card">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
    <div>
      <h2 style="margin:0;">Deteccion</h2>
      <div style="opacity:0.85;">Sube una imagen y genera detecciones automaticamente</div>
      <div style="opacity:0.75;font-size:0.9rem;">Umbrales fijos: deteccion=0.60, tipologia=0.35</div>
    </div>
    <div style="padding:6px 10px;border-radius:999px;background:rgba(124,58,237,0.18);border:1px solid rgba(124,58,237,0.35);">
      <span style="font-weight:600;">Pipeline: ON</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

uploaded = st.file_uploader("Imagen", type=["jpg", "jpeg", "png"])

DETECTOR_MODEL = Path("weights/best.pt")
TYPOLOGY_MODEL = Path("weights/yolov8n.pt")

CONF_DET = 0.60
CONF_TYPE = 0.35

def draw_boxes(img_bgr, dets: list[dict]):
    out = img_bgr.copy()
    for d in dets:
        x1, y1, x2, y2 = map(int, d["bbox_xyxy"])
        conf = float(d.get("confidence", 0.0))
        typ = d.get("typology", "unknown")
        color = typology_color_bgr(typ)

        label = f"{typ} ({int(conf * 100)}%)"
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, label, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return out

if uploaded:
    suffix = Path(uploaded.name).suffix if Path(uploaded.name).suffix else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        image_path = Path(tmp.name)

    with st.spinner("Analizando escena..."):
        t0 = time.time()
        bundle = analyze_scene(
            image_path=image_path,
            detector_model_path=DETECTOR_MODEL,
            typology_model_path=TYPOLOGY_MODEL,
            conf_det=CONF_DET,
            conf_type=CONF_TYPE,
        )
        infer_s = time.time() - t0

    img_bgr = cv2.imread(str(image_path))
    dets = extract_detections(bundle)
    img_det_bgr = draw_boxes(img_bgr, dets)

    left, right = st.columns(2)
    with left:
        st.subheader("Imagen original")
        st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)
    with right:
        st.subheader("Imagen con detecciones")
        st.image(cv2.cvtColor(img_det_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)

    total = len(dets)
    conf_avg = round(sum(float(d.get("confidence", 0.0)) for d in dets) / total, 2) if total else 0.0
    typs = [d.get("typology", "unknown") for d in dets]
    dominant = max(set(typs), key=typs.count) if typs else "-"

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
        st.metric("Vehiculos", total)
        st.markdown("</div>", unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
        st.metric("Confianza media", conf_avg)
        st.markdown("</div>", unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
        st.metric("Tipologia dominante", dominant)
        st.markdown("</div>", unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
        st.metric("Tiempo total (ms)", int(infer_s * 1000))
        st.markdown("</div>", unsafe_allow_html=True)

    save_last({
        "image_path": str(image_path),
        "bundle": bundle,
        "infer_s": infer_s,
    })
else:
    st.markdown("""
<div class="mye-card">
  <div style="font-weight:700;margin-bottom:6px;">Sube una imagen para empezar</div>
  <div style="opacity:0.85;">Aqui veras la comparativa Original vs Detecciones con etiqueta tipologia (porcentaje).</div>
</div>
""", unsafe_allow_html=True)
