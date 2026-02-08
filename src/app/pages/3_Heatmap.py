# src/app/pages/3_Heatmap.py
import streamlit as st
import numpy as np
import cv2
import pandas as pd

from src.app.state import load_last
from src.app.ui_helpers import (
    inject_global_ui,
    sidebar_block,
    section_title,
    page_header,
    section_label,
    kpi_card,
    extract_detections,
)

inject_global_ui()

with st.sidebar:
    sidebar_block()

    section_title("Navegacion")
    st.page_link("app.py", label="Inicio", icon="🏠")
    st.page_link("pages/1_Deteccion.py", label="Deteccion", icon="🎯")
    st.page_link("pages/2_Analitica.py", label="Analitica", icon="📊")
    st.page_link("pages/3_Heatmap.py", label="Mapa de calor", icon="🗺️")
    st.page_link("pages/4_Trazabilidad.py", label="Trazabilidad", icon="🔗")

    section_title("Consejo demo")
    st.caption("En Heatmap, ensena la imagen overlay + la tabla por tipologia.")

page_header(
    "Mapa de calor",
    "Mas intensidad = mas peso acumulado (confianza por bbox). Incluye resumen por tipologia.",
    badge="Heatmap",
)

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

heat_norm = (heat / heat.max() * 255).astype(np.uint8) if heat.max() > 0 else heat.astype(np.uint8)
heat_color = cv2.applyColorMap(heat_norm, cv2.COLORMAP_JET)
heat_color = cv2.GaussianBlur(heat_color, (0, 0), sigmaX=10, sigmaY=10)

alpha = 0.45
blend = cv2.addWeighted(img_bgr, 1.0 - alpha, heat_color, alpha, 0)

section_label("Heatmap")
st.image(cv2.cvtColor(blend, cv2.COLOR_BGR2RGB), use_container_width=True)

df = pd.DataFrame([{
    "typology": d.get("typology", "unknown"),
    "confidence": float(d.get("confidence", 0.0)),
} for d in dets])

section_label("Indicadores")
m1, m2, m3 = st.columns(3, gap="medium")
with m1:
    st.markdown(kpi_card("Detecciones", len(df)), unsafe_allow_html=True)
with m2:
    st.markdown(kpi_card("Conf media", round(df["confidence"].mean(), 2)), unsafe_allow_html=True)
with m3:
    top_typ = df["typology"].value_counts().idxmax() if len(df) else "-"
    st.markdown(kpi_card("Tipologia top", top_typ), unsafe_allow_html=True)

st.write("")
section_label("Resumen por tipologia (top)")
top = (
    df.groupby("typology")
      .agg(count=("typology", "size"), conf_mean=("confidence", "mean"))
      .sort_values("count", ascending=False)
      .head(6)
      .reset_index()
)
st.dataframe(top, use_container_width=True, height=260)
