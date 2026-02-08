import streamlit as st
import pandas as pd

from src.app.state import load_last
from src.app.ui_helpers import extract_detections

st.header("Analitica")

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
} for d in dets])

top = st.columns(4)
top[0].metric("Total detecciones", len(df))
top[1].metric("Conf media", round(df["confidence"].mean(), 2))
top[2].metric("Impact score", round(float(metrics.get("impact_score", 0.0)), 2))
top[3].metric("Congestion index", round(float(metrics.get("congestion_index", 0.0)), 2))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Conteo por tipologia")
    st.bar_chart(df["typology"].value_counts())

with c2:
    st.subheader("Confianza media por tipologia")
    st.bar_chart(df.groupby("typology")["confidence"].mean())
