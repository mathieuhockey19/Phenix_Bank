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
        with cols[i%4]: card(p,f"players-{p['id']}",st.session_state.lang)

def profile(pid):
    p=player_by_id(pid); info=totals(store,pid)
    if st.button(f'← {t("back_players",st.session_state.lang)}'): st.session_state.page="players"; st.rerun()
    left,right=st.columns([1,2])
    with left:
        photo=player_photo(p["photo_path"])
        if photo: st.image(photo,width="stretch")
    with right:
        st.markdown(f"# #{p['jersey_number']} {p['first_name']} {p['last_name']}")
        metrics(info,st.session_state.lang)
        if info["remaining"]>0:
            if st.button(t("pay",st.session_state.lang).upper(),type="primary",width="stretch"): st.session_state.show_wero=not st.session_state.get("show_wero",False)
            if st.session_state.get("show_wero"): payment_panel(info["remaining"],st.session_state.lang,f"{p['first_name']} {p['last_name']}")
    section(t("player_history",st.session_state.lang))
    fine_list([f for f in store["fines"] if f["player_id"]==pid])

def fine_list(rows):
    for f in sorted(rows,key=lambda x:x["fine_date"],reverse=True):
        st.markdown(f'<div class="fine-row"><span>{short_date(f["fine_date"])}</span><span>{fine_reason(f)}</span><b>{euro(f["final_amount"])}</b>{status_badge(f["status"])}</div>',unsafe_allow_html=True)
    if not rows: st.info(t("no_fines",st.session_state.lang))

def ranking():
    section(f'🏆 {t("ranking_title",st.session_state.lang)}')
    rows=player_rows(store); podium(rows[:3])
    headers=("Rang","Joueur","Nb. d’amendes","Total des amendes","Reste à payer") if st.session_state.lang=="FR" else ("Hely","Játékos","Bírságok száma","Bírságok összesen","Fizetendő")
    st.markdown(f'<div class="ranking-head"><span>{headers[0]}</span><span>{headers[1]}</span><span>{headers[2]}</span><span>{headers[3]}</span><span>{headers[4]}</span></div>',unsafe_allow_html=True)
    for i,p in enumerate(rows,1):
        photo=player_photo(p["photo_path"])
        avatar=f'<img src="{image_data_uri(photo)}" alt="">' if photo else '<span class="ranking-avatar">♟</span>'
        st.markdown(f'<div class="ranking-row"><strong class="rank">{i}</strong><div class="ranking-player">{avatar}<span><b>{p["first_name"]} {p["last_name"]}</b><small>#{p["jersey_number"]}</small></span></div><span data-label="{headers[2]}">{p["count"]}</span><strong data-label="{headers[3]}">{euro(p["total"])}</strong><strong class="balance" data-label="{headers[4]}">{euro(p["remaining"])}</strong></div>',unsafe_allow_html=True)

def history():
    section(t("all_fines",st.session_state.lang))
    names={p["id"]:f"{p['first_name']} {p['last_name']}" for p in store["players"]}
    statuses=st.multiselect(t("statuses",st.session_state.lang),["pending","paid","appeal","cancelled"],default=["pending","paid","appeal"],format_func=lambda value:t(value,st.session_state.lang))
    for f in sorted([x for x in store["fines"] if x["status"] in statuses],key=lambda x:x["fine_date"],reverse=True):
        st.markdown(f'<div class="fine-row"><span>{short_date(f["fine_date"])}</span><span><b>{names[f["player_id"]]}</b><br>{fine_reason(f)}</span><b>{euro(f["final_amount"])}</b>{status_badge(f["status"])}</div>',unsafe_allow_html=True)

def rules():
    section(t("locker_rules",st.session_state.lang))
    lang_key="label_fr" if st.session_state.lang=="FR" else "label_hu"
    for r in store["rules"]:
        if r["active"]: st.markdown(f'<div class="rule-card">{r[lang_key]} <b>{euro(r["amount"])}</b></div>',unsafe_allow_html=True)
    st.caption(t("rule_note",st.session_state.lang))

def admin():
    section(t("admin_area",st.session_state.lang))
    if not is_admin():
        if not configured_password():
            st.warning(t("demo_warning",st.session_state.lang))
            if st.button(t("open_demo",st.session_state.lang),type="primary"): st.session_state.admin_ok=True; st.rerun()
        else:
            with st.form("login"):
                password=st.text_input(t("password",st.session_state.lang),type="password")
                if st.form_submit_button(t("login",st.session_state.lang),type="primary"):
                    if login(password): st.rerun()
                    else: st.error(t("wrong_password",st.session_state.lang))
        return
    tabs=st.tabs([f'＋ {t("fines",st.session_state.lang)}',t("fines",st.session_state.lang),t("payments",st.session_state.lang),t("players",st.session_state.lang),t("rules",st.session_state.lang)])
    with tabs[0]: add_fine_ui()
    with tabs[1]: manage_fines()
    with tabs[2]: payments_ui()
    with tabs[3]: players_ui()
    with tabs[4]: rules_ui()

def add_fine_ui():
    st.subheader(t("add_fine",st.session_state.lang))
    if st.session_state.pop("fine_added",False):
        st.success(t("fine_added",st.session_state.lang))
    active=[p for p in store["players"] if p["active"]]
    if not active:
        st.info("Aucun joueur actif." if st.session_state.lang=="FR" else "Nincs aktív játékos.")
        return
    choices={f"#{p['jersey_number']} · {p['first_name']} {p['last_name']}":p["id"] for p in active}
    who=st.selectbox(f'1 · {t("player",st.session_state.lang)}',choices)
    rule_key="label_fr" if st.session_state.lang=="FR" else "label_hu"
    options={f"{r[rule_key]} — {euro(r['amount'])}":r for r in store["rules"] if r["active"]}
    options[t("other",st.session_state.lang)]={"id":None,"label_fr":t("other",st.session_state.lang),"amount":2}
    reason_label=st.selectbox(f'2 · {t("reason",st.session_state.lang)}',options)
    rule=options[reason_label]
    custom=st.text_input(t("custom_reason",st.session_state.lang)) if rule["id"] is None else rule["label_fr"]
    amount=st.number_input(t("base_amount",st.session_state.lang),min_value=.5,value=float(rule["amount"]),step=.5,disabled=rule["id"] is not None)
    match=st.toggle(t("match_day",st.session_state.lang))
    comment=st.text_area(t("comment_optional",st.session_state.lang))
    final=amount*(2 if match else 1)
    st.markdown(f'## {t("final_amount",st.session_state.lang)} : :orange[{euro(final)}]')
    if st.button(t("add_fine",st.session_state.lang).upper(),key="submit_fine_direct",type="primary",width="stretch"):
        if rule["id"] is None and not custom.strip():
            st.error("Indique le motif de l’amende." if st.session_state.lang=="FR" else "Add meg a bírság okát.")
        else:
            add_fine(store,choices[who],rule["id"],custom.strip(),amount,match,comment.strip())
            st.session_state.fine_added=True
            st.rerun()

def quick_fine():
    if st.button(
        "← Retour au site" if st.session_state.lang=="FR" else "← Vissza",
        key="close_quick_fine",
    ):
        st.session_state.quick_fine_open=False
        st.rerun()
    add_fine_ui()

def manage_fines():
    names={p["id"]:f"{p['first_name']} {p['last_name']}" for p in store["players"]}
    for f in sorted(store["fines"],key=lambda x:x["fine_date"],reverse=True):
        with st.expander(f"{short_date(f['fine_date'])} · {names[f['player_id']]} · {fine_reason(f)} · {euro(f['final_amount'])}"):
            reason=st.text_input(t("reason",st.session_state.lang),f["reason"],key=f"reason{f['id']}"); amount=st.number_input(t("amount",st.session_state.lang),.0,value=float(f["final_amount"]),key=f"amount{f['id']}")
            a,b,c,d=st.columns(4)
            if a.button(t("save",st.session_state.lang),key=f"save{f['id']}"): f["reason"],f["final_amount"]=reason,amount; remote_update(store,"fines",f["id"],{"custom_reason":reason,"final_amount":amount}); st.success(t("saved",st.session_state.lang))
            if b.button(t("paid",st.session_state.lang),key=f"paid{f['id']}"): update_status(store,f["id"],"paid"); st.rerun()
            if c.button(t("appeal",st.session_state.lang),key=f"appeal{f['id']}"): update_status(store,f["id"],"appeal"); st.rerun()
            if d.button(t("cancel",st.session_state.lang),key=f"cancel{f['id']}"): update_status(store,f["id"],"cancelled"); st.rerun()
            if f["status"]=="appeal":
                x,y=st.columns(2)
                if x.button(t("appeal_accepted",st.session_state.lang),key=f"aa{f['id']}"): update_status(store,f["id"],"appeal_accepted"); st.rerun()
                if y.button(t("appeal_refused",st.session_state.lang),key=f"ar{f['id']}"): update_status(store,f["id"],"appeal_refused"); st.rerun()
            if st.button(t("delete",st.session_state.lang),key=f"del{f['id']}"): remote_delete(store,"fines",f["id"]); store["fines"].remove(f); st.rerun()

def payments_ui():
    rows=player_rows(store); options={f"{p['first_name']} {p['last_name']} · {t('remaining',st.session_state.lang).lower()} {euro(p['remaining'])}":p for p in rows}
    with st.form("payment"):
        label=st.selectbox(t("player",st.session_state.lang),options); p=options[label]
        amount=st.number_input(t("amount",st.session_state.lang),min_value=.5,value=max(.5,float(p["remaining"])),step=.5)
        method=st.selectbox(t("method",st.session_state.lang),["Lydia","Wero","Espèces","Virement",t("other",st.session_state.lang)]); comment=st.text_input(t("comment",st.session_state.lang))
        if st.form_submit_button(t("record_payment",st.session_state.lang),type="primary"): add_payment(store,p["id"],amount,method,comment); st.success(t("payment_saved",st.session_state.lang))
    st.caption(t("payment_note",st.session_state.lang))

def players_ui():
    with st.form("new_player"):
        a,b,c=st.columns(3); first=a.text_input(t("first_name",st.session_state.lang)); last=b.text_input(t("last_name",st.session_state.lang)); number=c.number_input(t("number",st.session_state.lang),0,99)
        position=st.selectbox(t("position",st.session_state.lang),["Attaquant","Défenseur","Gardien"])
        if st.form_submit_button(t("add_player",st.session_state.lang)) and first and last:
            row={"first_name":first,"last_name":last.upper(),"jersey_number":number,"photo_path":"","position":position,"active":True}; created=remote_insert(store,"players",row); row["id"]=created["id"] if created else max(p["id"] for p in store["players"])+1; store["players"].append(row); st.rerun()
    for p in store["players"]:
        c1,c2=st.columns([5,1]); c1.write(f"#{p['jersey_number']} · {p['first_name']} {p['last_name']} · {p['position']}")
        if c2.button(t("active" if p["active"] else "inactive",st.session_state.lang),key=f"active{p['id']}"): p["active"]=not p["active"]; remote_update(store,"players",p["id"],{"active":p["active"]}); st.rerun()

def rules_ui():
    with st.form("new_rule"):
        label=st.text_input(t("new_rule",st.session_state.lang)); hu=st.text_input(t("hungarian_translation",st.session_state.lang)); amount=st.number_input(t("amount",st.session_state.lang),.5,100.,2.,.5)
        if st.form_submit_button(t("add",st.session_state.lang)) and label:
            row={"label_fr":label,"label_hu":hu or label,"amount":amount,"active":True}; created=remote_insert(store,"rules",row); row["id"]=created["id"] if created else max(r["id"] for r in store["rules"])+1; store["rules"].append(row); st.rerun()
    for r in store["rules"]:
        c1,c2,c3=st.columns([6,1,1]); c1.write(r["label_fr"] if st.session_state.lang=="FR" else r["label_hu"]); c2.write(euro(r["amount"]))
        if c3.button("✓" if r["active"] else "○",key=f"rule{r['id']}"): r["active"]=not r["active"]; remote_update(store,"rules",r["id"],{"active":r["active"]}); st.rerun()

if st.session_state.get("quick_fine_open") and is_admin():
    quick_fine()
elif st.session_state.get("mobile_admin_open"):
    admin()
elif st.session_state.get("mobile_rules_open"):
    rules()
elif st.session_state.get("payment_open"):
    payment_checkout()
elif page=="profile": profile(st.session_state.get("selected_player",1))
elif page=="home": home()
elif page=="players": players()
elif page=="ranking": ranking()
elif page=="history": history()
elif page=="rules": rules()
elif page=="admin": admin()




