import hmac
import streamlit as st

def is_admin(): return bool(st.session_state.get("admin_ok"))

def configured_password():
    try:
        return st.secrets.get("admin", {}).get("password", "")
    except st.errors.StreamlitSecretNotFoundError:
        return ""

def login(password):
    expected=configured_password()
    if expected and hmac.compare_digest(password, expected): st.session_state.admin_ok=True; return True
    return False
