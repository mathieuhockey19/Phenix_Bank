from copy import deepcopy
from datetime import date,datetime,timedelta
from pathlib import Path
import json
import re
import uuid
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
    if any(_apps_credentials()):
        st.session_state.store=_load_apps_script()
        return st.session_state.store
    if "store" not in st.session_state:
        st.session_state.store=_load_google_sheets() or _load_supabase() or deepcopy(_seed())
    return st.session_state.store

SHEET_NAMES={"players":"Joueurs","rules":"Règles","fines":"Amendes","payments":"Paiements"}
SHEET_HEADERS={
    "players":{"id":"Identifiant","first_name":"Prénom","last_name":"Nom","jersey_number":"Numéro","photo_path":"Photo","position":"Poste","active":"Actif"},
    "rules":{"id":"Identifiant","label_fr":"Motif (FR)","label_hu":"Motif (HU)","amount":"Montant (€)","active":"Actif"},
    "fines":{"id":"Identifiant","player_id":"Joueur (ID)","rule_id":"Règle (ID)","custom_reason":"Motif personnalisé","base_amount":"Montant de base (€)","final_amount":"Montant final (€)","match_day":"Jour de match","status":"Statut","fine_date":"Date","comment":"Commentaire"},
    "payments":{"id":"Identifiant","player_id":"Joueur (ID)","amount":"Montant (€)","payment_date":"Date","method":"Méthode","comment":"Commentaire"},
}

def _google_credentials():
    try:
        section=st.secrets.get("google_sheets", {})
        raw=section.get("service_account_json", "")
        return section.get("spreadsheet_id", ""), json.loads(raw) if raw else None
    except (st.errors.StreamlitSecretNotFoundError, json.JSONDecodeError):
        return "", None

@st.cache_resource
def _google_book(spreadsheet_id, credentials_json):
    import gspread
    credentials=json.loads(credentials_json)
    return gspread.service_account_from_dict(credentials).open_by_key(spreadsheet_id)

def _book():
    spreadsheet_id,credentials=_google_credentials()
    if not (spreadsheet_id and credentials): return None
    return _google_book(spreadsheet_id,json.dumps(credentials,sort_keys=True))

def _sheet_rows(table):
    rows=_book().worksheet(SHEET_NAMES[table]).get_all_records()
    headers=SHEET_HEADERS[table]
    result=[{field:row.get(label,"") for field,label in headers.items()} for row in rows]
    return [row for row in result if row.get("id") not in ("",None)]

def _as_bool(value):
    return value if isinstance(value,bool) else str(value).strip().lower() in {"true","vrai","1","oui"}

def _as_id(value):
    try: return int(value)
    except (TypeError,ValueError): return value

def _as_date(value):
    if isinstance(value,(int,float)):
        return date(1899,12,30)+timedelta(days=int(value))
    text=str(value).strip()[:10]
    for pattern in ("%Y-%m-%d","%d/%m/%Y"):
        try: return datetime.strptime(text,pattern).date()
        except ValueError: pass
    raise ValueError(f"Date Google Sheets invalide : {value}")

def _load_google_sheets():
    try:
        if not _book(): return None
        players=_sheet_rows("players"); rules=_sheet_rows("rules")
        fines=_sheet_rows("fines"); payments=_sheet_rows("payments")
        return _normalize_sheet_store({"players":players,"rules":rules,"fines":fines,"payments":payments}, "google_sheets")
    except Exception as exc:
        st.warning(f"Google Sheets indisponible, bascule en mode démo : {exc}")
        return None


def _normalize_sheet_store(data, backend):
        players=data["players"]; rules=data["rules"]; fines=data["fines"]; payments=data["payments"]
        for p in players:
            p["id"]=_as_id(p.get("id")); p["jersey_number"]=int(p.get("jersey_number") or 0)
            p["active"]=_as_bool(p.get("active",True)); p.setdefault("position","Attaquant")
        for r in rules:
            r["id"]=_as_id(r.get("id")); r["amount"]=float(r.get("amount") or 0); r["active"]=_as_bool(r.get("active",True))
        for f in fines:
            f["id"]=_as_id(f.get("id")); f["player_id"]=_as_id(f.get("player_id")); f["rule_id"]=_as_id(f.get("rule_id")) if f.get("rule_id") not in ("",None) else None
            f["base_amount"]=float(f.get("base_amount") or 0); f["final_amount"]=float(f.get("final_amount") or 0); f["match_day"]=_as_bool(f.get("match_day"))
            f["reason"]=f.get("custom_reason") or next((r["label_fr"] for r in rules if r["id"]==f.get("rule_id")),"Autre")
            f["fine_date"]=_as_date(f["fine_date"])
        for p in payments:
            p["id"]=_as_id(p.get("id")); p["player_id"]=_as_id(p.get("player_id")); p["amount"]=float(p.get("amount") or 0)
            p["payment_date"]=_as_date(p["payment_date"])
        return {"players":players,"rules":rules,"fines":fines,"payments":payments,"_remote":True,"_backend":backend}

def _apps_credentials():
    try:
        section=st.secrets.get("apps_script", {})
        return section.get("url", ""), section.get("api_key", "")
    except st.errors.StreamlitSecretNotFoundError:
        return "", ""

@st.cache_data(ttl=20, max_entries=4, show_spinner=False)
def _cached_apps_read(url, api_key):
    # Les deux paramètres isolent le cache par configuration.
    # cache_data fournit une copie indépendante à chaque session.
    return _apps_request("read")

def _apps_request(action, **payload):
    import requests
    url, key=_apps_credentials()
    if not (url.startswith("https://script.google.com/macros/s/") and url.endswith("/exec") and key):
        raise ValueError("Configuration Apps Script incomplète.")
    if action != "read": _cached_apps_read.clear()
    try:
        response=requests.post(url, json={"action":action,"api_key":key,**payload}, timeout=30)
        response.raise_for_status()
        result=response.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError("Apps Script inaccessible. Vérifiez le déploiement et réessayez.") from None
    if not result.get("ok"):
        raise RuntimeError("Apps Script a refusé la requête. Vérifiez la clé et les colonnes du Sheet.")
    if action != "read": _cached_apps_read.clear()
    return result["data"]

def _load_apps_script():
    try:
        from services.auth import configured_password
        if not configured_password():
            raise ValueError("Mot de passe admin manquant.")
        url, key=_apps_credentials()
        return _normalize_sheet_store(_cached_apps_read(url, key), "apps_script")
    except Exception:
        st.error("Connexion Google Sheets impossible. Vérifiez les Secrets, le mot de passe admin, le déploiement Apps Script et les colonnes du Sheet. Aucune donnée n’a été enregistrée.")
        st.stop()

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
    if store.get("_backend")=="apps_script":
        from services.auth import is_admin
        if not is_admin(): raise PermissionError("Accès admin requis.")
        return _apps_request("insert",table=table,payload=payload)
    if store.get("_backend")=="google_sheets":
        worksheet=_book().worksheet(SHEET_NAMES[table]); headers=worksheet.row_values(1)
        row={"id":str(uuid.uuid4()),**payload}
        fields={label:field for field,label in SHEET_HEADERS[table].items()}
        worksheet.append_row([row.get(fields.get(header,""),"") for header in headers],value_input_option="USER_ENTERED")
        return row
    if store.get("_remote"):
        return _client().table(table).insert(payload).execute().data[0]

def remote_update(store, table, row_id, payload):
    if store.get("_backend")=="apps_script":
        from services.auth import is_admin
        if not is_admin(): raise PermissionError("Accès admin requis.")
        _apps_request("update",table=table,row_id=str(row_id),payload=payload)
        return
    if store.get("_backend")=="google_sheets":
        worksheet=_book().worksheet(SHEET_NAMES[table]); headers=worksheet.row_values(1)
        cell=worksheet.find(str(row_id),in_column=1)
        labels=SHEET_HEADERS[table]
        for key,value in payload.items():
            label=labels.get(key)
            if label in headers: worksheet.update_cell(cell.row,headers.index(label)+1,value)
        return
    if store.get("_remote"):
        _client().table(table).update(payload).eq("id",row_id).execute()

def remote_delete(store, table, row_id):
    if store.get("_backend")=="apps_script":
        from services.auth import is_admin
        if not is_admin(): raise PermissionError("Accès admin requis.")
        _apps_request("delete",table=table,row_id=str(row_id))
        return
    if store.get("_backend")=="google_sheets":
        worksheet=_book().worksheet(SHEET_NAMES[table]); cell=worksheet.find(str(row_id),in_column=1)
        worksheet.delete_rows(cell.row)
        return
    if store.get("_remote"):
        _client().table(table).delete().eq("id",row_id).execute()

def using_supabase():
    return bool(_credentials()[0] and _credentials()[1])

def backend_name():
    active=st.session_state.get("store", {})
    if active.get("_backend") in {"apps_script","google_sheets"}: return "GOOGLE SHEETS"
    if active.get("_remote"): return "SUPABASE"
    return ""


