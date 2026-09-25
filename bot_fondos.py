"""Fondos con video real: Pexels API (gratis). Fallback: None (degradado local)."""
import os

import requests

CACHE = "fondos"
STOP = {
    "el", "la", "los", "las", "de", "del", "en", "que", "los", "una", "uno",
    "con", "por", "para", "como", "mas", "muy", "sin", "sobre", "esto",
    "esta", "estos", "estas", "the", "a", "y", "o", "se", "su", "al",
}

NICHO_QUERY = {
    "noticias": "news city crowd",
    "gaming": "neon gaming futuristic",
    "curiosidades": "mystery night cosmos",
    "anime": "tokyo neon night street",
    "futbol": "soccer stadium night fans",
    "economia": "city skyline night business",
    "finanzas": "stock market chart screen",
    "historia": "ancient castle dark cinematic",
    "ia_tech": "robot artificial intelligence neon",
}


def _keywords(tema, nicho):
    words = [w.strip(".,!?¿¡\"'").lower() for w in tema.split()]
    keys = [w for w in words if len(w) > 3 and w not in STOP]
    q = " ".join(keys[:4]) or NICHO_QUERY.get(nicho, "city night")
    return q


def buscar_fondo(tema, nicho="curiosidades"):
    """Un fondo (compat). Devuelve path o None."""
    fondos = buscar_fondos(tema, nicho, n=1)
    return fondos[0] if fondos else None


def _buscar_una(query, cachear=True):
    key = os.getenv("PEXELS_API_KEY", "")
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": key},
        params={"query": query, "per_page": 4, "orientation": "portrait", "size": "medium"},
        timeout=30,
    )
    r.raise_for_status()
    for v in r.json().get("videos", []):
        best, best_score = None, None
        for f in v.get("video_files", []):
            w, h = f.get("width", 0), f.get("height", 0)
            if w < 480:
                continue
            score = (1 if h > w else 0, -(w * h))
            if best_score is None or score > best_score:
                best, best_score = f["link"], score
        if best:
            dest = f"{CACHE}/{v.get('id', abs(hash(best)))}.mp4"
            if not (os.path.exists(dest) and os.path.getsize(dest) > 100_000):
                d = requests.get(best, timeout=120)
                d.raise_for_status()
                with open(dest, "wb") as fh:
                    fh.write(d.content)
            return dest
    return None


def buscar_fondos(tema, nicho="curiosidades", n=3, queries=None):
    """Un clip por query de la IA (inicio/desarrollo/final) o busqueda clasica.
    Devuelve lista de paths."""
    if not os.getenv("PEXELS_API_KEY", ""):
        print("Fondo: sin PEXELS_API_KEY -> degradado")
        return []
    os.makedirs(CACHE, exist_ok=True)
    qs = [q for q in (queries or []) if q][:n] or [_keywords(tema, nicho)]
    outs, vistos = [], set()
    for q in qs:
        if len(outs) >= n:
            break
        try:
            p = _buscar_una(q)
            if p and p not in vistos:
                vistos.add(p)
                outs.append(p)
        except Exception as e:
            print(f"Fondo query '{q}': {e}")
            continue
    if not outs:
        print(f"Fondo: Pexels sin resultados -> degradado")
        return []
    print(f"Fondo: {len(outs)} clips Pexels {qs}")
    return outs
