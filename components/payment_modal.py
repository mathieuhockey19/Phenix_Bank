import streamlit as st
from utils.formatting import euro

PAYMENT_URL = "https://pay.lydia.me/l?t=mathieud2529"

def payment_panel(amount, lang="FR", player_name=""):
    if amount <= 0:
        st.success("Tu es à jour, aucune amende à payer !" if lang == "FR" else "Nincs befizetendő bírságod!")
        return
    st.markdown(f"### Lydia · {euro(amount)}")
    st.write(
        f"Saisis **{euro(amount)}** sur la page Lydia."
        if lang == "FR" else f"A Lydia oldalon ezt az összeget add meg: **{euro(amount)}**."
    )
    if player_name:
        st.caption("Motif à indiquer :" if lang == "FR" else "Közlemény:")
        st.code(f"Amendes Phénix — {player_name}", language=None)
    st.link_button(
        "💳 Payer avec Lydia" if lang == "FR" else "💳 Fizetés Lydiával",
        PAYMENT_URL, type="primary", width="stretch",
    )
    st.caption(
        "Après réception, Mathieu enregistrera ton paiement. Ton solde sera mis à jour après validation."
        if lang == "FR" else "Mathieu a pénz beérkezése után rögzíti a befizetésedet. Az egyenleged a jóváhagyás után frissül."
    )

