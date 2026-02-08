# src/app/app.py
import streamlit as st

st.set_page_config(page_title="MyE", layout="wide")

GLOBAL_CSS = """
<style>
.block-container { padding-top: 1.1rem; padding-bottom: 1.1rem; }

section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
section[data-testid="stSidebar"] .stMarkdown { color: rgba(229,231,235,0.92); }

h1, h2, h3 { letter-spacing: -0.02em; }
h1 { margin-bottom: 0.2rem; }

.mye-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.22);
}

.mye-cta {
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  background: rgba(124,58,237,0.16);
  border: 1px solid rgba(124,58,237,0.34);
  border-radius: 16px;
  padding: 14px 16px;
}

.mye-kpi {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 10px 12px;
}

div[data-testid="stMetricLabel"] { font-size: 0.85rem; opacity: 0.85; }
div[data-testid="stMetricValue"] { font-size: 1.55rem; }

img { border-radius: 16px; }
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.sidebar.title("MyE")
st.sidebar.caption("Vehicle Detection System")

st.markdown("# MyE")
st.caption("Vehicle Detection and Typology")

st.markdown(
    """
<div class="mye-card">
  <h2 style="margin:0;">Inicio</h2>
  <div style="opacity:0.85;">
    Demo multipagina: Deteccion, Analitica, Heatmap, Trazabilidad.
    Empieza en Deteccion para procesar una imagen y desbloquear el resto de paginas.
  </div>
</div>
""",
    unsafe_allow_html=True
)

st.write("")

left, right = st.columns([2, 1])

with left:
    st.markdown(
        """
<div class="mye-cta">
  <div>
    <div style="font-size:1.05rem;font-weight:700;">Paso 1</div>
    <div style="opacity:0.9;">Ve a la pagina Deteccion y sube una imagen</div>
    <div style="opacity:0.75;font-size:0.9rem;">Umbrales fijos: deteccion=0.60, tipologia=0.35</div>
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    st.write("")

    colb1, colb2, colb3, colb4 = st.columns(4)
    with colb1:
        if st.button("Ir a Deteccion", use_container_width=True):
            st.switch_page("pages/1_Deteccion.py")
    with colb2:
        if st.button("Ir a Analitica", use_container_width=True):
            st.switch_page("pages/2_Analitica.py")
    with colb3:
        if st.button("Ir a Heatmap", use_container_width=True):
            st.switch_page("pages/3_Heatmap.py")
    with colb4:
        if st.button("Ir a Trazabilidad", use_container_width=True):
            st.switch_page("pages/4_Trazabilidad.py")

with right:
    st.markdown(
        """
<div class="mye-card">
  <div style="font-weight:700;margin-bottom:6px;">Flujo</div>
  <div style="opacity:0.85;">1) Deteccion + Tipologia</div>
  <div style="opacity:0.85;">2) Metricas</div>
  <div style="opacity:0.85;">3) Heatmap espacial</div>
  <div style="opacity:0.85;">4) Evidencia (hash + timestamp)</div>
</div>
""",
        unsafe_allow_html=True
    )
