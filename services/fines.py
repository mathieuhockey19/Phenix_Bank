from datetime import date
from services.database import remote_insert,remote_update

OPEN_STATUSES={"pending","appeal"}

def totals(store, player_id=None):
    rows=[f for f in store["fines"] if player_id is None or f["player_id"]==player_id]
    valid=[f for f in rows if f["status"]!="cancelled"]
    total=sum(float(f["final_amount"]) for f in valid)
    payments_total=sum(float(p["amount"]) for p in store["payments"] if player_id is None or p["player_id"]==player_id)
    status_paid_total=sum(float(f["final_amount"]) for f in valid if f["status"]=="paid")
    # Les deux parcours admin peuvent représenter le même règlement.
    # On retient le plus grand cumul pour refléter les amendes marquées payées
    # sans compter deux fois un paiement également saisi dans Paiements.
    paid=min(max(payments_total,status_paid_total),total)
    return {"total":total,"paid":paid,"remaining":max(total-paid,0),"count":len(valid)}

def player_rows(store):
    result=[]
    for player in store["players"]:
        item=dict(player); item.update(totals(store, player["id"])); result.append(item)
    return sorted(result,key=lambda p:(p["total"],p["count"]),reverse=True)

def add_fine(store, player_id, rule_id, reason, base_amount, match_day, comment=""):
    row={"player_id":player_id,"rule_id":rule_id,"custom_reason":reason if rule_id is None else None,"reason":reason,"base_amount":base_amount,"final_amount":base_amount*(2 if match_day else 1),"match_day":match_day,"status":"pending","fine_date":date.today(),"comment":comment}
    payload={k:(v.isoformat() if isinstance(v,date) else v) for k,v in row.items() if k!="reason"}
    created=remote_insert(store,"fines",payload)
    row["id"]=created["id"] if created else max([f["id"] for f in store["fines"]]+[0])+1
    store["fines"].append(row)

def update_status(store, fine_id, status):
    fine=next(f for f in store["fines"] if f["id"]==fine_id)
    if status=="appeal_refused": fine["status"],fine["final_amount"]="pending",fine["base_amount"]*2
    elif status=="appeal_accepted": fine["status"]="cancelled"
    else: fine["status"]=status
    remote_update(store,"fines",fine_id,{"status":fine["status"],"final_amount":fine["final_amount"]})

