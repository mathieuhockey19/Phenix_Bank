from datetime import date, datetime

def euro(value):
    return f"{float(value):,.2f} €".replace(",", " ").replace(".00", "")

def short_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return str(value)
