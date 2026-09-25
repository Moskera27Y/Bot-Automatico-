"""Escudos (ESPN CDN) y avatares (Wikimedia Commons, licencia libre) con cache."""
import hashlib
import os
import re

import requests
from PIL import Image, ImageDraw, ImageFont

H = {"User-Agent": "KALADORnewsbot/1.0 (news summaries; local use)"}


def _get(url, params=None, timeout=20, intentos=3):
    import time as _t
    err = None
    for i in range(intentos):
        try:
            r = requests.get(url, params=params, headers=H, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            err = e
            _t.sleep(2 + i * 2)
    raise err
MALAS = ("logo", "kit", "jersey", "stadium", "trophy", "tifo", "banner",
         "signature", "firma", "autograph", "seal", "coin", "stamp")


def escudo(team_id, logo_url):
    """Escudo oficial servido por ESPN. Devuelve path o None."""
    if not logo_url:
        return None
    os.makedirs("escudos", exist_ok=True)
    dest = f"escudos/{team_id}.png"
    try:
        if os.path.exists(dest) and os.path.getsize(dest) > 5000:
            return dest
        r = requests.get(logo_url, headers=H, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        return dest
    except Exception as e:
        print(f"Escudo fallo ({e})")
        return None


def foto_partido(local, vis):
    """Foto libre del enfrentamiento/estadio (Commons). Devuelve path o None."""
    import hashlib as _hl
    os.makedirs("avatares", exist_ok=True)
    tag = _hl.md5(f"partido{local}{vis}".encode()).hexdigest()[:10]
    for ext in (".jpg", ".png"):
        if os.path.exists(f"avatares/p_{tag}{ext}") and os.path.getsize(f"avatares/p_{tag}{ext}") > 20000:
            return f"avatares/p_{tag}{ext}"
    for q in (f"{local} {vis}", f"{local} stadium"):
        try:
            s = _get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "format": "json", "list": "search",
                "srsearch": q, "srnamespace": 6, "srlimit": 10}, headers=H, timeout=20).json()
            pick = None
            for x in s.get("query", {}).get("search", []):
                t = x["title"].lower()
                if any(b in t for b in MALAS + ("signature", "map", "chart", "graph")):
                    continue
                pick = x["title"]
                break
            if not pick:
                continue
            ii = _get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "format": "json", "titles": pick, "prop": "imageinfo",
                "iiprop": "url", "iiurlwidth": 900}, headers=H, timeout=20).json()
            info = next(iter(ii["query"]["pages"].values()))["imageinfo"][0]
            r = requests.get(info["thumburl"], headers=H, timeout=30)
            r.raise_for_status()
            dest = f"avatares/p_{tag}.jpg"
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"Foto partido: {pick[:60]}")
            return dest
        except Exception as e:
            print(f"Foto partido ({e})")
            continue
    return None


def avatar_iniciales(nombre, dest, size=300):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=(40, 20, 90, 255),
              outline=(255, 200, 0), width=max(4, size // 60))
    ini = "".join(p[0] for p in nombre.split() if p)[:2].upper() or "K"
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size // 3)
    except Exception:
        f = ImageFont.load_default()
    bb = d.textbbox((0, 0), ini, font=f)
    x = (size - (bb[2] - bb[0])) // 2
    y = (size - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((x, y), ini, font=f, fill=(255, 200, 0))
    img.save(dest)
    return dest


def circulo(path, size=160):
    """Recorta imagen a circulo con borde dorado."""
    img = Image.open(path).convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    ImageDraw.Draw(out).ellipse([2, 2, size - 3, size - 3], outline=(255, 200, 0), width=5)
    return out


def avatar_persona(nombre):
    """Foto libre de la persona (Wikimedia Commons). Devuelve (path, credito).
    Si no hay foto libre, iniciales (sin credito)."""
    os.makedirs("avatares", exist_ok=True)
    tag = hashlib.md5(nombre.encode()).hexdigest()[:10]
    dest = f"avatares/{tag}.png"
    credf = dest + ".credito.txt"
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        cred = open(credf, encoding="utf-8").read() if os.path.exists(credf) else ""
        return dest, cred
    try:
        s = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "list": "search",
            "srsearch": nombre, "srnamespace": 6, "srlimit": 10}, headers=H, timeout=20).json()
        pick = None
        for x in s.get("query", {}).get("search", []):
            t = x["title"].lower()
            if any(b in t for b in MALAS):
                continue
            pick = x["title"]
            break
        if not pick:
            raise RuntimeError("sin foto libre")
        ii = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "titles": pick, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 400}, headers=H, timeout=20).json()
        info = next(iter(ii["query"]["pages"].values()))["imageinfo"][0]
        r = requests.get(info["thumburl"], headers=H, timeout=30)
        r.raise_for_status()
        tmp = dest + ".tmp"
        with open(tmp, "wb") as f:
            f.write(r.content)
        circulo(tmp, 300).save(dest)
        os.remove(tmp)
        autor = re.sub(r"<[^>]+>", "", info.get("extmetadata", {}).get("Artist", {}).get("value", "Wikimedia")).strip()[:80]
        cred = f"Foto: {autor} (Wikimedia Commons)"
        open(credf, "w", encoding="utf-8").write(cred)
        print(f"Avatar: {nombre} -> Commons")
        return dest, cred
    except Exception as e:
        print(f"Avatar {nombre}: {e} -> iniciales")
        return avatar_iniciales(nombre, dest), ""
