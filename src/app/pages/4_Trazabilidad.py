import streamlit as st
import json

from src.app.state import load_last
from src.evidence.hashing import hash_bundle
from src.evidence.register import register_evidence

st.header("Trazabilidad")

run = load_last()
if not run:
    st.info("No hay ultima ejecucion. Ve a Deteccion y sube una imagen.")
    st.stop()

bundle = run["bundle"]

# 1) Minimo garantizado: hash + timestamp
e = hash_bundle(bundle)

c1, c2 = st.columns(2)
with c1:
    st.text("Analysis hash (sha256)")
    st.code(e["sha256"])

with c2:
    st.text("Timestamp UTC")
    st.code(e["timestamp_utc"])

st.download_button(
    "Descargar comprobante (JSON)",
    data=json.dumps({"analysis_hash": e["sha256"], "timestamp_utc": e["timestamp_utc"]}, indent=2).encode("utf-8"),
    file_name="mye_evidence_min.json",
    mime="application/json"
)

st.divider()

# 2) Intento de registro on-chain (opcional)
st.subheader("Registro (opcional)")
if st.button("Registrar en blockchain"):
    try:
        result = register_evidence(bundle)
        st.success("Registro completado.")
        st.json(result)
    except Exception as ex:
        st.warning("No se pudo registrar on-chain. El hash y timestamp ya quedan generados.")
        st.code(str(ex))
