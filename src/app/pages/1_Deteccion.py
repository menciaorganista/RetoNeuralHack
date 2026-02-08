from pathlib import Path
import tempfile
import time

import streamlit as st
import cv2

from src.pipeline.analyze import analyze_scene
from src.app.state import save_last
from src.app.ui_helpers import extract_detections, typology_color_bgr

st.header("Deteccion")

uploaded = st.file_uploader(
    "Sube una imagen (auto-analisis al subir)",
    type=["jpg", "jpeg", "png"]
)

# Mantener compacto (no scroll). Model paths fijos:
DETECTOR_MODEL = Path("weights/best.pt")       # tu modelo MyE
TYPOLOGY_MODEL = Path("weights/yolov8n.pt")    # modelo COCO para tipologia (ajusta si usas otro)

conf_det = st.slider("Conf deteccion", 0.05, 0.90, 0.25, 0.05)
conf_type = st.slider("Conf tipologia", 0.05, 0.90, 0.25, 0.05)

def draw_boxes(img_bgr, dets: list[dict]):
    out = img_bgr.copy()
    for d in dets:
        x1, y1, x2, y2 = map(int, d["bbox_xyxy"])
        conf = float(d.get("confidence", 0.0))
        typ = d.get("typology", d.get("class_name", "unknown"))
        color = typology_color_bgr(typ)

        label = f"{typ} ({int(conf * 100)}%)"
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, label, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return out

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        image_path = Path(tmp.name)

    with st.spinner("Analizando escena..."):
        t0 = time.time()
        bundle = analyze_scene(
            image_path=image_path,
            detector_model_path=DETECTOR_MODEL,
            typology_model_path=TYPOLOGY_MODEL,
            conf_det=conf_det,
            conf_type=conf_type,
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vehiculos", total)
    c2.metric("Confianza media", conf_avg)
    c3.metric("Tipologia dominante", dominant)
    c4.metric("Tiempo total (ms)", int(infer_s * 1000))

    save_last({
        "image_path": str(image_path),
        "bundle": bundle,
        "infer_s": infer_s
    })
else:
    st.caption("Sube una imagen para ver original vs detecciones (tipologia y confianza en la etiqueta).")
