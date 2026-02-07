import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import json
import tempfile
import streamlit as st

from src.vision.infer import run_inference, save_outputs
from src.pipeline.run_metrics import main as run_metrics_main
from src.pipeline.add_evidence import main as add_evidence_main
from src.config import RUNS_DIR, ANALYSIS_DIR



st.set_page_config(page_title="MyE Traffic UAV", layout="wide")
st.title("MyE = Sistema Inteligente de Analisis de Trafico (UAV)")

st.sidebar.header("Configuracion")
model_path = st.sidebar.text_input(
    "Ruta del modelo (.pt)",
    value=str(Path("weights/MyE_best.pt").resolve())
)
conf = st.sidebar.slider("Confianza minima", 0.05, 0.90, 0.25, 0.05)

st.write("Sube una imagen (captura UAV o similar) y obtendras detecciones, metricas y evidencia (hash + timestamp).")

uploaded = st.file_uploader("Imagen", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    # Guardar temporalmente la imagen subida
    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = Path(tmp.name)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Imagen original")
        st.image(str(tmp_path), use_container_width=True)

    if st.button("Analizar"):
        # 1) Inferencia
        analysis = run_inference(tmp_path, Path(model_path), conf_threshold=conf)

        # Guardamos outputs usando el nombre original (para que sea bonito)
        # Copiamos/guardamos con el nombre del upload
        img_for_outputs = RUNS_DIR / uploaded.name
        img_for_outputs.parent.mkdir(parents=True, exist_ok=True)
        img_for_outputs.write_bytes(tmp_path.read_bytes())

        # Guardar imagen con boxes y JSON detecciones
        save_outputs(img_for_outputs, analysis)

        det_json_path = ANALYSIS_DIR / f"{Path(uploaded.name).stem}.json"

        # 2) Metricas
        run_metrics_main(det_json_path, img_for_outputs)

        bundle_path = ANALYSIS_DIR / f"{Path(uploaded.name).stem}_bundle.json"

        # 3) Evidencia (hash + timestamp)
        add_evidence_main(bundle_path)

        evidence_path = ANALYSIS_DIR / f"{Path(uploaded.name).stem}_bundle_evidence.json"

        with col2:
            st.subheader("Imagen con detecciones")
            out_img = RUNS_DIR / uploaded.name
            st.image(str(out_img), use_container_width=True)

        # Mostrar resultados
        st.subheader("Resultados")
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        bundle_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

        st.write("Detecciones:", bundle["detections"]["num_detections"])
        st.json(bundle["metrics"])

        st.subheader("Evidencia verificable")
        st.code(bundle_evidence["evidence"]["sha256"])
        st.write("Timestamp UTC:", bundle_evidence["evidence"]["timestamp_utc"])

        st.caption("Archivos generados en reports/runs y reports/analysis_json")
