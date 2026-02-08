from __future__ import annotations

import streamlit as st


# -----------------------------
# Data helpers (unchanged)
# -----------------------------
def extract_detections(bundle: dict) -> list[dict]:
    d = bundle.get("detections", {})
    if isinstance(d, dict) and "detections" in d and isinstance(d["detections"], list):
        return d["detections"]
    if "detections" in bundle and isinstance(bundle["detections"], list):
        return bundle["detections"]
    return []


def typology_color_bgr(typ: str) -> tuple[int, int, int]:
    palette = {
        "car": (60, 220, 120),
        "bus": (0, 190, 255),
        "truck": (80, 80, 255),
        "motorcycle": (220, 90, 220),
        "bicycle": (255, 160, 60),
        "unknown": (180, 180, 180),
    }
    return palette.get(typ, (0, 255, 0))


# -----------------------------
# UI styles (midpoint)
# -----------------------------
def inject_ui_styles() -> None:
    st.markdown(
        """
<style>
:root{
  --bg: #f3f5fb;
  --panel: rgba(255,255,255,0.96);
  --panel2: rgba(255,255,255,0.86);
  --border: rgba(15,23,42,0.14);

  --text: rgba(15,23,42,0.94);
  --muted: rgba(15,23,42,0.72);

  --brand: #5b5af7;
  --brand2: #24b6a8;

  --radius: 18px;
  --shadow: 0 14px 34px rgba(15,23,42,0.12);
  --shadow2: 0 8px 22px rgba(15,23,42,0.10);

}

/* Background = keep the pretty one */
.stApp{
  background:
    radial-gradient(1200px 700px at 12% 6%, rgba(91,90,247,0.14), transparent 55%),
    radial-gradient(1100px 700px at 88% 10%, rgba(36,182,168,0.10), transparent 55%),
    linear-gradient(180deg, var(--bg), #ffffff 100%);
  color: var(--text);
}

.block-container{
  padding-top: 3rem;
  padding-bottom: 1.75rem;
  max-width: 1500px;
}

/* Sidebar = keep the good one */
div[data-testid="stSidebarNav"]{ display:none; }

section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.78);
  border-right: 1px solid var(--border);
}

/* Sidebar header card */
.mye-side-header{
  border: 1px solid var(--border);
  background: var(--panel2);
  border-radius: var(--radius);
  padding: 12px 12px;
  box-shadow: var(--shadow2);
  margin-bottom: 12px;
}
.mye-side-title{
  font-size: 16px;
  font-weight: 950;
  margin: 0;
  letter-spacing: -0.01em;
  color: var(--text);
}
.mye-side-sub{
  margin: 6px 0 0 0;
  font-size: 12px;
  color: var(--muted);
}

/* Page header (no big card, but still strong) */
.mye-page-title{
  margin-bottom: 10px;
}
.mye-page-title h1{
  margin: 0;
  font-size: 38px;
  font-weight: 950;
  letter-spacing: -0.03em;
  line-height: 1.02;
  color: var(--text);
}
.mye-page-title p{
  margin: 10px 0 0 0;
  color: var(--muted);
  font-size: 16px;
  max-width: 980px;
}
.mye-badge{
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(91,90,247,0.12);
  border: 1px solid rgba(91,90,247,0.24);
  font-weight: 900;
  color: rgba(15,23,42,0.86);
  white-space: nowrap;
}

/* Section label (small, clean) */
.mye-section-label{
  margin-top: 18px;
  margin-bottom: 10px;
  font-size: 12px;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: rgba(15,23,42,0.65);
  font-weight: 950;
}

/* KPI mini-cards ONLY (these we keep) */
.mye-kpi-card{
  border-radius: 16px;
  background: rgba(255,255,255,0.86);
  border: 1px solid rgba(15,23,42,0.10);
  box-shadow: 0 10px 30px rgba(15,23,42,0.07);
  padding: 14px 14px 12px 14px;
}
.mye-kpi-label{
  font-size: 12px;
  color: rgba(15,23,42,0.60);
  font-weight: 900;
  margin-bottom: 6px;
  letter-spacing: 0.02em;
}
.mye-kpi-value{
  font-size: 26px;
  font-weight: 950;
  letter-spacing: -0.02em;
  color: rgba(15,23,42,0.95);
  line-height: 1.1;
}
.mye-kpi-foot{
  margin-top: 6px;
  font-size: 13px;
  color: rgba(15,23,42,0.55);
}

/* Buttons look nice on light background */
.stButton > button, div[data-testid="stDownloadButton"] > button{
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(91,90,247,0.26) !important;
  background: linear-gradient(180deg, rgba(91,90,247,0.18), rgba(91,90,247,0.10)) !important;
  color: rgba(15,23,42,0.94) !important;
  font-weight: 950 !important;
  padding: 0.70rem 0.95rem !important;
}

/* Images + code */
img{ border-radius: 14px; }
.stCodeBlock pre{ border-radius: 14px !important; }

/* IMPORTANT: remove big border wrappers (so no "big cards") */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* De-nest common widget frames */
div[data-testid="stFileUploader"] section{
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
div[data-testid="stTabs"] div[role="tabpanel"]{
  border: none !important;
  background: transparent !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

/* === Escala tipografica global (mas legible) === */
html, body, [class*="css"] {
  font-size: 20px;
}

/* === Titulo principal === */
.mye-page-title h1{
  font-size: 2.4rem;
}

/* === Subtitulo === */
.mye-page-title p{
  font-size: 1.05rem;
}

/* === Labels de seccion === */
.mye-section-label{
  font-size: 0.78rem;
}

/* === Valores KPI === */
.mye-kpi-value{
  font-size: 1.5rem;
}


</style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# New API (pages)
# -----------------------------
def page_header(title: str, subtitle: str = "", badge: str | None = None) -> None:
    inject_ui_styles()
    badge_html = f'<span class="mye-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
<div class="mye-page-title" style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">
  <div>
    <h1>{title}</h1>
    <p>{subtitle}</p>
  </div>
  <div>{badge_html}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<div class="mye-section-label">{text}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str | int | float, foot: str = "") -> str:
    foot_html = f'<div class="mye-kpi-foot">{foot}</div>' if foot else ""
    return f"""
<div class="mye-kpi-card">
  <div class="mye-kpi-label">{label}</div>
  <div class="mye-kpi-value">{value}</div>
  {foot_html}
</div>
"""


# -----------------------------
# Backward compatible API
# -----------------------------
def inject_global_ui() -> None:
    inject_ui_styles()


def header_block(title: str, subtitle: str, badge: str = "") -> None:
    page_header(title, subtitle, badge if badge else None)


def section_title(text: str) -> None:
    section_label(text)


def sidebar_block() -> None:
    st.sidebar.markdown(
        """
<div class="mye-side-header">
  <div class="mye-side-title">MyE</div>
  <div class="mye-side-sub">Smart cities · trafico UAV · analitica · evidencia</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card(*args, **kwargs):
    return st.container()
