# src/app/pages/4_Trazabilidad.py
import json
import streamlit as st

from src.app.state import load_last
from src.blockchain.register import register_evidence

st.markdown("""
<div class="mye-card">
  <h2 style="margin:0;">Trazabilidad</h2>
  <div style="opacity:0.85;">Hash + timestamp + registro on-chain (si esta disponible)</div>
</div>
""", unsafe_allow_html=True)
st.write("")

run = load_last()
if not run:
    st.info("No hay ultima ejecucion. Ve a Deteccion y sube una imagen.")
    st.stop()

bundle = run["bundle"]

# Compute evidence now (local always, on-chain optional)
result = register_evidence(bundle)
evidence = result.get("evidence", {})
chain = result.get("chain", {})

# Big block 1
st.markdown('<div class="mye-card">', unsafe_allow_html=True)
st.subheader("Evidencia (hash del analisis)")
st.write("Este hash permite verificar la integridad del bundle.")
st.code(str(evidence.get("analysis_hash", "")))
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# Big block 2
st.markdown('<div class="mye-card">', unsafe_allow_html=True)
st.subheader("Timestamp y registro")

c1, c2 = st.columns(2)
with c1:
    st.text("Timestamp UTC")
    st.code(str(evidence.get("timestamp_utc", "")))
with c2:
    st.text("Scene ID / Model")
    st.code(f'{evidence.get("scene_id","unknown")} | {evidence.get("model_version","MyE_v1")}')

st.write("")
st.text("Resultado on-chain")
st.code(json.dumps(chain, indent=2) if chain else "Sin datos")

st.write("")
st.download_button(
    "Descargar comprobante (JSON)",
    data=json.dumps(result, indent=2).encode("utf-8"),
    file_name="mye_evidence_onchain.json",
    mime="application/json",
    use_container_width=True
)
st.markdown("</div>", unsafe_allow_html=True)
