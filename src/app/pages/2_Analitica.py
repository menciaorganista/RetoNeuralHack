# src/app/pages/2_Analitica.py
import streamlit as st
import pandas as pd
import cv2

from src.app.state import load_last
from src.app.ui_helpers import (
    inject_global_ui,
    sidebar_block,
    section_title,
    page_header,
    section_label,
    kpi_card,
    extract_detections,
    typology_color_bgr,
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
    st.caption("En Analitica, ensena KPIs y graficas. La tabla esta en Heatmap.")

page_header(
    "Analitica",
    "Metricas y resumen visual de la ultima escena analizada. Sin tabla aqui (esta en Heatmap).",
)

run = load_last()
if not run:
    st.info("No hay ultima ejecucion. Ve a Deteccion y sube una imagen.")
    st.stop()

bundle = run["bundle"]
metrics = bundle.get("metrics", {})
dets = extract_detections(bundle)

if not dets:
    st.warning("No hay detecciones en la ultima imagen.")
    st.stop()

df = pd.DataFrame([{
    "typology": d.get("typology", "unknown"),
    "confidence": float(d.get("confidence", 0.0)),
    "x1": d["bbox_xyxy"][0],
    "y1": d["bbox_xyxy"][1],
    "x2": d["bbox_xyxy"][2],
    "y2": d["bbox_xyxy"][3],
} for d in dets])

img_bgr = cv2.imread(run["image_path"])

def draw_boxes_small(img_bgr, df: pd.DataFrame):
    out = img_bgr.copy()
    for _, r in df.iterrows():
        x1, y1, x2, y2 = map(int, [r["x1"], r["y1"], r["x2"], r["y2"]])
        typ = str(r["typology"])
        conf = float(r["confidence"])
        color = typology_color_bgr(typ)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, f"{typ} ({int(conf*100)}%)", (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return out

img_det = draw_boxes_small(img_bgr, df)

section_label("Indicadores")
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.markdown(kpi_card("Detecciones", len(df), "Total"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Conf media", round(df["confidence"].mean(), 2), "Promedio"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Impact score", round(float(metrics.get("impact_score", 0.0)), 2), "Indicador"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Congestion", round(float(metrics.get("congestion_index", 0.0)), 2), "Indicador"), unsafe_allow_html=True)

st.write("")
section_label("Escena")
st.image(cv2.cvtColor(img_det, cv2.COLOR_BGR2RGB), use_container_width=True)

st.write("")
section_label("Distribucion")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Conteo por tipologia")
    st.bar_chart(df["typology"].value_counts())
with c2:
    st.subheader("Confianza media por tipologia")
    st.bar_chart(df.groupby("typology")["confidence"].mean())
