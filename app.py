from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Phénix Bank",page_icon="🔥",layout="wide",initial_sidebar_state="expanded")
ROOT=Path(__file__).parent
st.markdown(f"<style>{(ROOT/'styles/main.css').read_text()}</style>",unsafe_allow_html=True)

from components.metrics import metrics
from components.navigation import navigation
from components.payment_modal import payment_panel
from components.player_card import card
from components.podium import podium
from services.auth import configured_password,is_admin,login
from services.database import backend_name,get_store,remote_delete,remote_insert,remote_update
from services.fines import add_fine,player_rows,totals,update_status
from services.payments import add_payment
from utils.formatting import euro,short_date
from utils.images import image_data_uri,player_photo
from utils.translations import t

store=get_store()
st.session_state.setdefault("lang","FR")

with st.sidebar:
    st.markdown("<div style='font-size:4rem;text-align:center'>🔥</div><h2 style='text-align:center;margin-top:0'>PHÉNIX</h2>",unsafe_allow_html=True)
    page=navigation(st.session_state.lang)
    st.markdown("---")
    st.caption("MORE THAN A TEAM · 26/27")

head1,head2=st.columns([5,1])
with head1:
    st.markdown(f'<div class="brand"><h1>PHÉNIX BANK</h1><p>{t("season",st.session_state.lang).upper()} · {t("tagline",st.session_state.lang).upper()}</p></div>',unsafe_allow_html=True)
with head2:
    st.session_state.lang=st.segmented_control("Langue",["FR","HU"],default=st.session_state.lang,label_visibility="collapsed") or "FR"
    st.markdown(f'<span class="demo-badge">● {backend_name() or t("demo_mode",st.session_state.lang)}</span>',unsafe_allow_html=True)

payment_label = "💳 Je paye mes amendes" if st.session_state.lang == "FR" else "💳 Befizetem a bírságaimat"
if st.button(payment_label, key="open_payment_checkout", type="primary", width="stretch"):
    st.session_state.payment_open = True
    st.session_state.quick_fine_open = False
    st.session_state.mobile_admin_open = False
    st.session_state.mobile_rules_open = False

rules_label = (
    "← Retour au site" if st.session_state.get("mobile_rules_open")
    else ("📋 Voir les règles" if st.session_state.lang == "FR" else "📋 Szabályok")
)
if st.button(rules_label, key="open_mobile_rules", width="stretch"):
    st.session_state.mobile_rules_open = not st.session_state.get("mobile_rules_open",False)
    st.session_state.payment_open = False
    st.session_state.mobile_admin_open = False
    st.session_state.quick_fine_open = False
    st.rerun()

admin_label = (
    "← Retour au site" if st.session_state.get("mobile_admin_open")
    else ("🔐 Espace admin" if st.session_state.lang == "FR" else "🔐 Admin felület")
)
if st.button(admin_label, key="open_mobile_admin", width="stretch"):
    st.session_state.mobile_admin_open = not st.session_state.get("mobile_admin_open",False)
    st.session_state.payment_open = False
    st.session_state.quick_fine_open = False
    st.session_state.mobile_rules_open = False
    st.rerun()

if is_admin() and st.button(
    "➕ Ajouter une amende" if st.session_state.lang == "FR" else "➕ Bírság hozzáadása",
    key="open_quick_fine",
    width="stretch",
):
    st.session_state.quick_fine_open = True
    st.session_state.payment_open = False
    st.session_state.mobile_admin_open = False
    st.session_state.mobile_rules_open = False
    st.rerun()

def payment_checkout():
    lang = st.session_state.lang
    st.subheader("Je paye mes amendes" if lang == "FR" else "Bírságok befizetése")
    if st.button("← Retour au site" if lang == "FR" else "← Vissza", key="close_payment_checkout"):
        st.session_state.payment_open = False
        st.rerun()
    # Un joueur inactif peut encore avoir un solde à régler.
    choices = sorted(store["players"], key=lambda p: (p["first_name"], p["last_name"]))
    if not choices:
        st.info("Aucun joueur disponible." if lang == "FR" else "Nincs elérhető játékos.")
        return
    by_id = {p["id"]: p for p in choices}
    pid = st.selectbox(
        "Qui es-tu ?" if lang == "FR" else "Ki vagy?",
        list(by_id), index=None,
        placeholder="Sélectionne ton nom" if lang == "FR" else "Válaszd ki a neved",
        format_func=lambda value: f"#{by_id[value]['jersey_number']} · {by_id[value]['first_name']} {by_id[value]['last_name']}",
        key="payment_player_id",
    )
    if pid is None:
        return
    player = by_id[pid]
    name = f"{player['first_name']} {player['last_name']}"
    info = totals(store, pid)
    st.metric("Reste à payer" if lang == "FR" else "Fizetendő", euro(info["remaining"]))
    payment_panel(info["remaining"], lang, name)

def section(title): st.markdown(f'<h2 class="section-title">{title}</h2>',unsafe_allow_html=True)
def status_badge(status):
    label=t(status,st.session_state.lang)
    return f'<span class="status {status}">{label}</span>'
def player_by_id(pid): return next(p for p in store["players"] if p["id"]==pid)
def fine_reason(fine):
    if st.session_state.lang=="HU" and fine.get("rule_id"):
        return next((r["label_hu"] for r in store["rules"] if r["id"]==fine["rule_id"]),fine["reason"])
    return fine["reason"]

def home():
    metrics(totals(store),st.session_state.lang)
    ranked=player_rows(store)
    section(t("top",st.session_state.lang)); podium(ranked[:3])
    section(t("locker_room",st.session_state.lang))
    cols=st.columns(4)
    for i,p in enumerate(ranked[:8]):
        with cols[i%4]: card(p,f"home-{p['id']}",st.session_state.lang)

def players():
    section(t("players",st.session_state.lang))
    query=st.text_input("Recherche",placeholder=t("search",st.session_state.lang),label_visibility="collapsed").lower()
    rows=[p for p in player_rows(store) if not query or query in f"{p['first_name']} {p['last_name']}".lower()]
    cols=st.columns(4)
    for i,p in enumerate(rows):