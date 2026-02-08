# src/app/pages/3_Heatmap.py
import streamlit as st
import numpy as np
import cv2
import pandas as pd

from src.app.state import load_last
from src.app.ui_helpers import extract_detections, typology_color_bgr

st.markdown("""
<div class="mye-card">
  <h2 style="margin:0;">Heatmap</h2>
  <div style="opacity:0.85;">Mas intensidad = mas peso acumulado (confianza por bbox)</div>
</div>
""", unsafe_allow_html=True)
st.write("")

run = load_last()
if not run:
    st.info("No hay ultima ejecucion. Ve a Deteccion y sube una imagen.")
    st.stop()

image_path = run["image_path"]
bundle = run["bundle"]
dets = extract_detections(bundle)

if not dets:
    st.warning("No hay detecciones en la ultima imagen.")
    st.stop()

img_bgr = cv2.imread(image_path)
h, w = img_bgr.shape[:2]

# Heat accumulation (weight = confidence)
heat = np.zeros((h, w), dtype=np.float32)
for d in dets:
    x1, y1, x2, y2 = map(int, d["bbox_xyxy"])
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        continue
    heat[y1:y2, x1:x2] += float(d.get("confidence", 0.0))

if heat.max() > 0:
    heat_norm = (heat / heat.max() * 255).astype(np.uint8)
else:
    heat_norm = heat.astype(np.uint8)

# Colormap overlay (like your example)
heat_color = cv2.applyColorMap(heat_norm, cv2.COLORMAP_JET)
alpha = 0.55
blend = cv2.addWeighted(img_bgr, 1.0 - alpha, heat_color, alpha, 0)

# Optional: draw bbox on top for context (keeps the look from your example)
for d in dets:
    x1, y1, x2, y2 = map(int, d["bbox_xyxy"])
    typ = d.get("typology", "unknown")
    conf = float(d.get("confidence", 0.0))

    # white thick bbox + thin colored bbox
    cv2.rectangle(blend, (x1, y1), (x2, y2), (245, 245, 245), 2)
    cv2.rectangle(blend, (x1, y1), (x2, y2), typology_color_bgr(typ), 1)

    cv2.putText(
        blend,
        f"{typ} ({int(conf * 100)}%)",
        (x1, max(0, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (245, 245, 245),
        1
    )

st.markdown('<div class="mye-card">', unsafe_allow_html=True)
st.image(cv2.cvtColor(blend, cv2.COLOR_BGR2RGB), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Compact metrics row
df = pd.DataFrame([{
    "typology": d.get("typology", "unknown"),
    "confidence": float(d.get("confidence", 0.0)),
} for d in dets])

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
    st.metric("Detecciones", len(df))
    st.markdown("</div>", unsafe_allow_html=True)
with m2:
    st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
    st.metric("Conf media", round(df["confidence"].mean(), 2))
    st.markdown("</div>", unsafe_allow_html=True)
with m3:
    top_typ = df["typology"].value_counts().idxmax() if len(df) else "-"
    st.markdown('<div class="mye-kpi">', unsafe_allow_html=True)
    st.metric("Tipologia top", top_typ)
    st.markdown("</div>", unsafe_allow_html=True)
