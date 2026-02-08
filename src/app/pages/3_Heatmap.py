import streamlit as st
import numpy as np
import cv2
import pandas as pd

from src.app.state import load_last
from src.app.ui_helpers import extract_detections

st.header("Heatmap de detecciones")
st.caption("Mas intensidad = mas peso acumulado. Peso = confianza por bbox.")

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

if heat.max() > 0:
    heat = heat / heat.max()

overlay = np.zeros((h, w, 3), dtype=np.uint8)
overlay[:, :, 2] = (heat * 255).astype(np.uint8)  # canal rojo

alpha = (heat * 0.55).astype(np.float32)[:, :, None]
base = img_bgr.astype(np.float32)
ov = overlay.astype(np.float32)
blend = (base * (1.0 - alpha) + ov * alpha).astype(np.uint8)

left, right = st.columns([3, 2])
with left:
    st.image(cv2.cvtColor(blend, cv2.COLOR_BGR2RGB), use_container_width=True)

with right:
    df = pd.DataFrame([{
        "typology": d.get("typology", "unknown"),
        "confidence": float(d.get("confidence", 0.0)),
    } for d in dets])

    st.subheader("Metricas")
    st.metric("Total detecciones", len(df))
    st.metric("Confianza media", round(df["confidence"].mean(), 2))

    st.text("Conteo por tipologia")
    st.dataframe(df["typology"].value_counts().rename("count"), use_container_width=True, height=220)
