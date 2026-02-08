from pathlib import Path
import tempfile
import time

import streamlit as st
import cv2

from src.pipeline.analyze import analyze_scene
from src.app.state import save_last
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
    st.caption("Empieza en Deteccion: carga una imagen y luego ve a Analitica y Heatmap.")

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


page_header(
    "Deteccion",
    "Sube una imagen y genera detecciones automaticamente. Comparativa clara + KPIs.",
    badge=f"Umbrales: det={CONF_DET:.2f} · tip={CONF_TYPE:.2f}",
)

left, right = st.columns([0.42, 0.58], gap="large")

with left:
    section_label("Entrada")
    uploaded = st.file_uploader("Imagen (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

    st.write("")
    section_label("Guia rapida")
    st.write("1. Sube una imagen.")
    st.write("2. Se ejecuta deteccion + tipologia.")
    st.write("3. Revisa comparativa y KPIs.")

with right:
    section_label("Vista")
    if not uploaded:
        st.info("Sube una imagen para ver la comparativa y los KPIs.")
        st.stop()

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

    total = len(dets)
    conf_avg = round(sum(float(d.get("confidence", 0.0)) for d in dets) / total, 2) if total else 0.0
    typs = [d.get("typology", "unknown") for d in dets]
    dominant = max(set(typs), key=typs.count) if typs else "-"

    st.write("")
    section_label("Indicadores")
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(kpi_card("Vehiculos", total, "Total detectado"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Confianza media", conf_avg, "Promedio confianza"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Tipologia dominante", dominant, "Mas frecuente"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Tiempo (ms)", int(infer_s * 1000), "Inferencia"), unsafe_allow_html=True)

    st.write("")
    section_label("Comparativa")
    t1, t2 = st.tabs(["Original", "Detecciones"])
    with t1:
        st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)
    with t2:
        st.image(cv2.cvtColor(img_det_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)

    save_last({"image_path": str(image_path), "bundle": bundle, "infer_s": infer_s})
