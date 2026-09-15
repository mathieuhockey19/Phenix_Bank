from datetime import date
from services.database import remote_insert

def add_payment(store, player_id, amount, method, comment=""):
    row={"player_id":player_id,"amount":float(amount),"payment_date":date.today(),"method":method,"comment":comment}
    created=remote_insert(store,"payments",{**row,"payment_date":row["payment_date"].isoformat()})
    row["id"]=created["id"] if created else max([p["id"] for p in store["payments"]]+[0])+1
    store["payments"].append(row)
