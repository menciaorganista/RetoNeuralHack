import json
import streamlit as st

from src.app.state import load_last
from src.blockchain.register import register_evidence
from src.app.ui_helpers import (
    inject_global_ui,
    sidebar_block,
    section_title,
    page_header,
    section_label,
    kpi_card,
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
    st.caption("Aqui ensena: hash, timestamp y descarga del comprobante JSON.")

page_header(
    "Trazabilidad",
    "Evidencia de integridad del analisis: hash + timestamp + resultado de registro.",
    badge="Evidencia",
)

run = load_last()
if not run:
    st.info("No hay ultima ejecucion. Ve a Deteccion y sube una imagen.")
    st.stop()

bundle = run["bundle"]

result = register_evidence(bundle)
evidence = result.get("evidence", {})
chain = result.get("chain", {})

analysis_hash = str(evidence.get("analysis_hash", ""))
timestamp_utc = str(evidence.get("timestamp_utc", ""))
scene_id = str(evidence.get("scene_id", "unknown"))
model_version = str(evidence.get("model_version", "MyE_v1"))

hash_ok = bool(analysis_hash)
ts_ok = bool(timestamp_utc)
chain_ok = bool(chain)

section_label("Estado")
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    st.markdown(kpi_card("Hash", "OK" if hash_ok else "N/A"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("Timestamp", "OK" if ts_ok else "N/A"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("On-chain", "OK" if chain_ok else "N/A"), unsafe_allow_html=True)

st.write("")
section_label("Evidencia")
st.subheader("Hash del analisis")
st.code(analysis_hash or "Sin hash")

st.write("")
section_label("Registro")
left, right = st.columns([1, 1.2], gap="large")

with left:
    st.subheader("Timestamp y contexto")
    st.write("Timestamp UTC")
    st.code(timestamp_utc or "Sin timestamp")

    st.write("Scene ID / Model")
    st.code(f"{scene_id} | {model_version}")

    st.write("")
    st.download_button(
        "Descargar comprobante (JSON)",
        data=json.dumps(result, indent=2).encode("utf-8"),
        file_name="mye_evidence_onchain.json",
        mime="application/json",
        use_container_width=True,
    )

with right:
    st.subheader("Resultado on-chain")
    st.code(json.dumps(chain, indent=2) if chain else "Sin datos")
