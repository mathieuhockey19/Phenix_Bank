from pathlib import Path
import base64
import mimetypes

ROOT = Path(__file__).resolve().parents[1]

def player_photo(path):
    candidate = ROOT / path
    return str(candidate) if candidate.exists() else None

def wero_qr():
    path = ROOT / "assets/qr/wero.png"
    return str(path) if path.exists() else None

def image_data_uri(path):
    if not path: return ""
    mime=mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"
