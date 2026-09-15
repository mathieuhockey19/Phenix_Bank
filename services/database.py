from copy import deepcopy
from datetime import date
from pathlib import Path
import re
import streamlit as st

PLAYER_META=[("Mathieu","DERUELLE","Attaquant"),("Dimitri","JUAN","Gardien"),("Alex","CHRETIEN","Défenseur"),("Alexis","GOURVENNEC","Attaquant"),("Alois","JONCOUX","Attaquant"),("Arthur","VALOGNES","Défenseur"),("Axel","BOISSEAU","Attaquant"),("Benji","TELLIER","Défenseur"),("Diego","DURAN","Attaquant"),("Lorinc","FARKAS","Attaquant"),("Matyas","SZOLLOSI","Défenseur"),("Maxime","RIDDE","Gardien"),("Morgan","GUYONVARCH","Attaquant"),("Rémi","BOISSEAU","Défenseur"),("Thomas","BOYARD","Attaquant"),("William","GARNIER","Défenseur")]

def _player_assets():
    root=Path(__file__).resolve().parents[1]; folder=root/"assets/players"; cutouts=folder/"cutouts"
    rows=[]
    for idx,(first,last,position) in enumerate(PLAYER_META,1):
        ascii_first="Remi" if first=="Rémi" else first
        matches=sorted(folder.glob(f"{ascii_first}.{last}_*.*"))
        source=next((p for p in matches if p.suffix.lower() in {".jpg",".jpeg",".png"}),None)
        number=int(re.search(r"_(\d+)",source.stem).group(1)) if source and re.search(r"_(\d+)",source.stem) else 0
        cutout=cutouts/f"{source.stem}_cutout.png" if source else None
        photo=cutout if cutout and cutout.exists() else source
        rows.append((idx,first,last,number,str(photo.relative_to(root)) if photo else "",position))
    return rows
RULES = [
 (1,"Non port de pantalon à l’entraînement","Edzésnadrág hiánya",2),(2,"Retard à l’arrivée","Késés",2),
 (3,"Retard pour sortir de la salle après l’entraînement","Késői távozás",2),(4,"Oubli de la tenue de match","Mezfelszerelés hiánya",2),
 (5,"Oubli du maillot d’entraînement","Edzőmez hiánya",2),(6,"Casier non rangé / ouvert / déborde","Rendetlen szekrény",2),
 (7,"No show à un entraînement / match","Igazolatlan hiányzás",5),(8,"Pack anniversaire / Pack 3× Benders non payé","Ki nem fizetett csomag",5),
 (9,"Non nettoyage des gourdes par les Benders","Kulacsok nincsenek elmosva",10),
]

def _seed():
    players=[{"id":i,"first_name":f,"last_name":l,"jersey_number":n,"photo_path":p,"position":pos,"active":True} for i,f,l,n,p,pos in _player_assets()]
    rules=[{"id":i,"label_fr":fr,"label_hu":hu,"amount":a,"active":True} for i,fr,hu,a in RULES]
    return {"players":players,"rules":rules,"fines":[],"payments":[]}

def get_store():
    if "store" not in st.session_state:
        st.session_state.store=_load_supabase() or deepcopy(_seed())
    return st.session_state.store

def _credentials():
    try:
        section=st.secrets.get("supabase", {})
        return section.get("url", ""), section.get("service_role_key", "")
    except st.errors.StreamlitSecretNotFoundError:
        return "", ""

def _client():
    url,key=_credentials()
    if not (url and key): return None
    from supabase import create_client
    return create_client(url,key)

def _load_supabase():
    client=_client()
    if not client: return None
    try:
        players=client.table("players").select("*").order("last_name").execute().data
        rules=client.table("rules").select("*").order("created_at").execute().data
        fines=client.table("fines").select("*").order("fine_date",desc=True).execute().data
        payments=client.table("payments").select("*").order("payment_date",desc=True).execute().data
        for p in players: p.setdefault("position","Attaquant")
        for f in fines:
            f["reason"]=f.get("custom_reason") or next((r["label_fr"] for r in rules if r["id"]==f.get("rule_id")),"Autre")
            f["fine_date"]=date.fromisoformat(f["fine_date"])
        for p in payments: p["payment_date"]=date.fromisoformat(p["payment_date"])
        return {"players":players,"rules":rules,"fines":fines,"payments":payments,"_remote":True}
    except Exception as exc:
        st.warning(f"Supabase indisponible, bascule en mode démo : {exc}")
        return None

def remote_insert(store, table, payload):
    if store.get("_remote"):
        return _client().table(table).insert(payload).execute().data[0]

def remote_update(store, table, row_id, payload):
    if store.get("_remote"):
        _client().table(table).update(payload).eq("id",row_id).execute()

def remote_delete(store, table, row_id):
    if store.get("_remote"):
        _client().table(table).delete().eq("id",row_id).execute()

def using_supabase():
    return bool(_credentials()[0] and _credentials()[1])
