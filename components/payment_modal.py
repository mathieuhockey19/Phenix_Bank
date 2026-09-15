import streamlit as st
from utils.formatting import euro
from utils.images import wero_qr
from utils.translations import t

def payment_panel(amount,lang="FR"):
    st.markdown(f"### Wero · {euro(amount)}")
    qr=wero_qr()
    if qr: st.image(qr,width=260)
    else: st.info(t("wero_missing",lang))
    st.caption(t("wero_help",lang))
