"""Détourage déterministe des portraits, sans génération ni modification des visages."""
from pathlib import Path
import re
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/players"
OUT=SOURCE/"cutouts"
OUT.mkdir(exist_ok=True)

def matte(rgb):
    a=rgb.astype(np.float32)
    r,g,b=a[...,0],a[...,1],a[...,2]
    # Les JPG utilisent un écran vert; les PNG fournis utilisent un fond blanc.
    green_score=g-np.maximum(r,b)
    if np.mean(green_score>28)>.20:
        # La composante bleue du fond éclairé peut être forte : une combinaison
        # pondérée retire aussi ces halos cyan sans attaquer le maillot marine.
        key=g-(.55*r)-(.25*b)
        alpha=np.clip((48-key)/40,0,1)*255
        alpha=np.where((g>70)&(g>r*.98)&(key>5),alpha,255)
        # Despill uniquement sur les pixels semi-transparents du bord.
        edge=(alpha>0)&(alpha<255)
        a[...,1]=np.where(edge,np.minimum(g,np.maximum(r,b)*1.05),g)
    else:
        whiteness=np.minimum(np.minimum(r,g),b)
        spread=np.maximum(np.maximum(r,g),b)-whiteness
        alpha=np.clip((252-whiteness)/22,0,1)*255
        alpha=np.where((whiteness>205)&(spread<24),alpha,255)
    # Les joueurs posent face caméra : entre les deux bords du sujet, on
    # protège les couleurs du maillot (bleu clair compris) contre la clé.
    final=alpha.copy()
    solid=alpha>245
    for y in range(final.shape[0]):
        xs=np.flatnonzero(solid[y])
        if len(xs)>20:
            left,right=np.percentile(xs,[2,98]).astype(int)
            final[y,left:right+1]=255
    return Image.fromarray(final.astype("uint8")).filter(ImageFilter.GaussianBlur(0.7))

def process(path):
    image=Image.open(path).convert("RGB")
    image.thumbnail((1400,1800),Image.Resampling.LANCZOS)
    pixels=np.asarray(image)
    rgba=image.convert("RGBA"); rgba.putalpha(matte(pixels))
    alpha=np.asarray(rgba.getchannel("A"))
    # Un seuil franc évite que le léger halo du fond blanc définisse le
    # cadrage des cinq PNG et réduise artificiellement le joueur.
    r,g,b=pixels[...,0],pixels[...,1],pixels[...,2]
    spread=np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b)
    white_source=np.mean((np.minimum(np.minimum(r,g),b)>235)&(spread<20))>.25
    content=((np.minimum(np.minimum(r,g),b)<205)|(spread>38)) if white_source else (alpha>180)
    # Ignore les rares pixels de bruit isolés du fond lors du calcul du cadre.
    valid_rows=np.where(content.sum(axis=1)>max(12,image.width*.015))[0]
    valid_cols=np.where(content.sum(axis=0)>max(12,image.height*.015))[0]
    ys,xs=np.where(content)
    if len(valid_rows): ys=valid_rows
    if len(valid_cols): xs=valid_cols
    if not len(xs): raise ValueError(f"Sujet non détecté: {path.name}")
    crop=rgba.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    scale=min(790/crop.width,1030/crop.height)
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",(900,1100),(0,0,0,0))
    canvas.alpha_composite(crop,((900-crop.width)//2,1100-crop.height))
    stem=re.sub(r"\.(jpe?g|png)$","",path.name,flags=re.I)
    output=OUT/f"{stem}_cutout.png"
    canvas.save(output,optimize=True)
    return output

if __name__=="__main__":
    for path in sorted(SOURCE.iterdir()):
        if path.is_file() and path.suffix.lower() in {".jpg",".jpeg",".png"}:
            print(process(path).relative_to(ROOT))
