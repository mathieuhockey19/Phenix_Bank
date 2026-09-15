import streamlit as st
from utils.formatting import euro
from utils.translations import t

def metrics(data, lang):
    cols=st.columns(4)
    specs=[("◉",t("pot",lang),euro(data["total"]),"gold"),("✓",t("paid",lang),euro(data["paid"]),"green"),("⌛",t("remaining",lang),euro(data["remaining"]),"red"),("♟",t("fines",lang),str(data["count"]),"white")]
    for col,(icon,label,value,tone) in zip(cols,specs):
        col.markdown(f'<div class="metric-card"><span class="metric-icon {tone}">{icon}</span><div><small>{label}</small><strong class="{tone}">{value}</strong></div></div>',unsafe_allow_html=True)
