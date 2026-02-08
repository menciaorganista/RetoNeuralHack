# src/app/app.py
import streamlit as st

from src.app.ui_helpers import (
    inject_global_ui,
    sidebar_block,
    header_block,
    section_title,
)

st.set_page_config(page_title="MyE", page_icon="🛰️", layout="wide")

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

header_block(
    "MyE",
    "Aplicacion de deteccion y analisis de trafico desde UAV para smart cities. Flujo guiado: Deteccion = Analitica = Heatmap = Evidencia.",
    badge="Demo ready",
)

has_last = ("last" in st.session_state) or ("last_bundle" in st.session_state)

st.write("")
left, right = st.columns([0.62, 0.38], gap="large")

with left:
    section_title("Resumen de demo")
    st.write(
        "MyE procesa una imagen y genera: detecciones, tipologias, metricas, mapa de calor espacial y evidencia de integridad."
    )
    st.write("Recomendacion: empieza en Deteccion y luego revisa Analitica y Heatmap.")

    st.write("")
    section_title("Acciones rapidas")

    a1, a2 = st.columns(2, gap="medium")
    a3, a4 = st.columns(2, gap="medium")

    with a1:
        if st.button("Ir a Deteccion", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Deteccion.py")
    with a2:
        if st.button("Ir a Analitica", use_container_width=True, disabled=not has_last):
            st.switch_page("pages/2_Analitica.py")
    with a3:
        if st.button("Ir a Heatmap", use_container_width=True, disabled=not has_last):
            st.switch_page("pages/3_Heatmap.py")
    with a4:
        if st.button("Ir a Evidencia", use_container_width=True, disabled=not has_last):
            st.switch_page("pages/4_Trazabilidad.py")

    if not has_last:
        st.caption("Tip: carga una imagen en Deteccion para desbloquear la demo completa.")

with right:
    section_title("Flujo")
    st.write("1) Deteccion + tipologia")
    st.write("2) Metricas e indicadores")
    st.write("3) Heatmap espacial")
    st.write("4) Evidencia (hash + timestamp)")

    st.write("")
    section_title("Estado")
    st.write("Ultimo analisis cargado: si" if has_last else "Ultimo analisis cargado: no")
    if not has_last:
        st.caption("No hay analisis aun. Sube una imagen en Deteccion.")
