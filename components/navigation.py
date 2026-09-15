import streamlit as st
from utils.translations import t

PAGES=[("home","⌂"),("players","♟"),("ranking","🏆"),("history","◷"),("rules","▤"),("admin","⚙")]

def _navigate():
    st.session_state.page=st.session_state.nav_page

def navigation(lang):
    current=st.session_state.get("page","home")
    menu_page="players" if current=="profile" else current
    valid_pages=[key for key,_ in PAGES]
    if "nav_page" not in st.session_state:
        st.session_state.nav_page=menu_page
    elif current!="profile" and st.session_state.nav_page!=current:
        # Synchronise les navigations déclenchées hors sidebar.
        st.session_state.nav_page=current
    st.radio(
        "Navigation",valid_pages,
        format_func=lambda key:f"{dict(PAGES)[key]}  {t(key,lang)}",
        key="nav_page",on_change=_navigate,label_visibility="collapsed",
    )
    return st.session_state.get("page","home")
