from pathlib import Path
from functools import lru_cache
from io import BytesIO
import base64
import mimetypes

ROOT = Path(__file__).resolve().parents[1]

def player_photo(path):
    candidate = ROOT / path
    return str(candidate) if candidate.is_file() else None

def wero_qr():
    path = ROOT / "assets/qr/wero.png"
    return str(path) if path.is_file() else None

def image_data_uri(path):
    if not path: return ""
    source = Path(path).resolve()
    # Le QR est conservé tel quel. Seuls les portraits sont compressés.
    is_portrait = source.is_relative_to((ROOT / "assets/players").resolve())
    stamp = source.stat()
    return _encoded_image(str(source), stamp.st_mtime_ns, stamp.st_size, is_portrait)

@lru_cache(maxsize=64)
def _encoded_image(path, modified_ns, size, is_portrait):
    source = Path(path)
    if is_portrait:
        from PIL import Image, ImageOps
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert("RGBA")
            image.thumbnail((420, 514), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="WEBP", quality=75, method=4)
            data = output.getvalue()
        mime = "image/webp"
    else:
        data = source.read_bytes()
        mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"
