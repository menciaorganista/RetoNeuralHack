# src/app/pages/2_Analitica.py
import streamlit as st
import pandas as pd
import cv2

from src.app.state import load_last
from src.app.ui_helpers import extract_detections, typology_color_bgr

st.markdown("""
<div class="mye-card">
  <h2 style="margin:0;">Analitica</h2>
  <div style="opacity:0.85;">Metricas y resumen visual de la ultima escena analizada</div>
</div>
""", unsafe_allow_html=True)
st.write("")

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
    "class_name": d.get("class_name", "unknown"),
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

top_left, top_right = st.columns([1.2, 1])
with top_left:
    st.markdown('<div class="mye-card">', unsafe_allow_html=True)
    st.subheader("Escena (referencia)")
    st.image(cv2.cvtColor(img_det, cv2.COLOR_BGR2RGB), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="mye-card">', unsafe_allow_html=True)
    st.subheader("KPIs")
    k1, k2 = st.columns(2)
    with k1:
        st.metric("Detecciones", len(df))
        st.metric("Conf media", round(df["confidence"].mean(), 2))
    with k2:
        st.metric("Occupancy", round(float(metrics.get("occupancy_ratio", 0.0)), 3))
        st.metric("Density / MP", round(float(metrics.get("density_per_megapixel", 0.0)), 3))

    st.write("")
    st.metric("Impact score", round(float(metrics.get("impact_score", 0.0)), 2))
    st.metric("Congestion index", round(float(metrics.get("congestion_index", 0.0)), 2))
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

c1, c2, c3 = st.columns([1.2, 1.2, 1])

with c1:
    st.markdown('<div class="mye-card">', unsafe_allow_html=True)
    st.subheader("Conteo por tipologia")
    st.bar_chart(df["typology"].value_counts())
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="mye-card">', unsafe_allow_html=True)
    st.subheader("Confianza media por tipologia")
    st.bar_chart(df.groupby("typology")["confidence"].mean())
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="mye-card">', unsafe_allow_html=True)
    st.subheader("Tabla (top)")
    top = (
        df.groupby("typology")
          .agg(count=("typology", "size"), conf_mean=("confidence", "mean"))
          .sort_values("count", ascending=False)
          .head(6)
          .reset_index()
    )
    st.dataframe(top, use_container_width=True, height=240)
    st.markdown("</div>", unsafe_allow_html=True)
