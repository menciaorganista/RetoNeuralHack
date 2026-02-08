import streamlit as st

KEY = "mye_last"

def save_last(payload: dict) -> None:
    st.session_state[KEY] = payload

def load_last() -> dict | None:
    return st.session_state.get(KEY)
