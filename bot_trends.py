"""Detector de tendencias 100% gratis (sin API keys)."""
import feedparser
import requests
import random
from datetime import datetime, date, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0"}

LIGAS = ["col.1", "esp.1", "eng.1", "uefa.champions"]

# Banco evergreen que siempre viraliza en Shorts ES/LATAM
EVERGREEN = {
    "curiosidades": [
        "3 datos prohibidos de la historia que no te enseñaron en la escuela",
        "Lo que pasa en tu cerebro cuando no puedes dormir",
        "El experimento que salió mal y cambió el mundo",
        "Por qué nunca debes buscar esto en Google a las 3am",
        "El dato que te hará ver el dinero de otra forma",
    ],
    "noticias": [],
    "gaming": [
        "5 trucos secretos que solo los pros usan",
        "El error que te hace perder todas las partidas",
        "El clip más épico de la semana",
        "Esto pasa cuando subestimas a un noob",
        "Top 3 momentos que parecen fake pero son reales",
    ],
    "anime": [
        "El anime que todos estan viendo esta temporada",
        "El final que nadie vio venir",
        "El protagonista mas roto del anime actual",
    ],
    "finanzas": [
        "El error de dinero que casi todos cometen",
        "Como la inflacion te roba sin que lo notes",
        "Lo que los bancos no quieren que sepas",
        "Por que tu sueldo rinde menos cada mes",
        "El truco de los ricos para no perder dinero",
    ],
    "historia": [
        "El dia que cambio la historia y nadie recuerda",
        "El imperio que desaparecio sin dejar rastro",
        "La traicion que cambio un pais para siempre",
        "El misterio historico que nadie resolvio",
        "Lo que realmente paso ese dia que todos celebran",
    ],
    "ia_tech": [
        "La IA que hace esto mejor que un humano",
        "El truco de IA que nadie esta usando",
        "Lo que acaba de anunciar la industria tech",
    ],
}

def google_trends_es(limit=5):
    """Lee RSS de Google Trends España + México."""
    temas = []
    for geo in ["ES", "MX", "US"]:
        try:
            url = f"https://trends.google.com/trending/rss?geo={geo}"
            feed = feedparser.parse(url)
            for e in feed.entries[:limit]:
                temas.append({"titulo": e.title, "fuente": f"GoogleTrends-{geo}", "fecha": str(datetime.now().date())})
        except Exception:
            continue
    return temas

def google_news(limit=5):
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=es-419&gl=MX&ceid=MX:es-419")
        return [{"titulo": e.title.split(" - ")[0], "fuente": "GoogleNews", "fecha": str(datetime.now().date())} for e in feed.entries[:limit]]
    except Exception:
        return []

def reddit_viral(limit=5):
    temas = []
    subs = ["AskReddit", "memes", "gaming", "curiosidades", "mexico", "es"]
    for s in subs:
        try:
            r = requests.get(f"https://www.reddit.com/r/{s}/hot.json?limit={limit}", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                for p in r.json()["data"]["children"]:
                    t = p["data"]["title"]
                    if len(t) > 15:
                        temas.append({"titulo": t, "fuente": f"reddit r/{s}", "fecha": str(datetime.now().date())})
        except Exception:
            continue
    return temas

def futbol_hoy(limit=5):
    """Partidos FINALIZADOS hoy/ayer (ESPN, gratis): resultado + goleadores reales."""
    out = []
    for liga in LIGAS:
        for off in (0, -1):
            try:
                fecha = (date.today() + timedelta(days=off)).strftime("%Y%m%d")
                r = requests.get(
                    f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard",
                    params={"dates": fecha}, headers=HEADERS, timeout=15)
                for ev in r.json(). get("events", []):
                    comp = ev["competitions"][0]
                    if comp.get("status", {}).get("type", {}).get("state") != "post":
                        continue
                    comps = sorted(comp["competitors"], key=lambda c: c.get("order", 0))
                    h, a = comps[0], comps[1]
                    hn, an = h["team"]["shortDisplayName"], a["team"]["shortDisplayName"]
                    hs, aws = h.get("score", "?"), a.get("score", "?")
                    goles = []
                    for d in comp.get("details", []):
                        if d.get("scoringPlay"):
                            ats = d.get("athletesInvolved", [])
                            quien = (ats[0].get("shortName") or ats[0].get("displayName", "")) if ats else ""
                            goles.append(f"{quien} {d.get('clock', {}).get('displayValue', '')}".strip())
                    hechos = f"Resultado final: {hn} {hs}-{aws} {an}."
                    if goles:
                        hechos += " Goles: " + ", ".join(goles[:5]) + "."
                    rojas = sum(1 for d in comp.get("details", []) if d.get("redCard"))
                    if rojas:
                        hechos += f" Hubo {rojas} tarjeta(s) roja(s)."
                    out.append({"titulo": f"{hn} {hs}-{aws} {an}: resumen del partido",
                                "fuente": f"ESPN-{liga}", "fecha": str(date.today()),
                                "hechos": hechos, "nicho": "futbol",
                                "marcador": {"local": hn, "vis": an, "gl": hs, "gv": aws,
                                             "goles": goles[:4],
                                             "logo_local": h["team"].get("logo"),
                                             "logo_vis": a["team"].get("logo"),
                                             "id_local": h["team"].get("id"),
                                             "id_vis": a["team"].get("id")}})
            except Exception:
                continue
    # priorizar marcadores con mas goles / clasicos
    out.sort(key=lambda t: len(t.get("hechos", "")), reverse=True)
    return out[:limit]


def _news_search(query, fuente, limit=5, min_len=25):
    """Google News search RSS generico."""
    try:
        import io
        url = (f"https://news.google.com/rss/search?q={query}&hl=es-419&gl=MX&ceid=MX:es-419")
        r = requests.get(url, headers=HEADERS, timeout=20)
        feed = feedparser.parse(io.BytesIO(r.content))
        out = []
        for e in feed.entries[:limit * 2]:
            tit = e.title.split(" - ")[0].strip()
            if len(tit) < min_len:
                continue
            out.append({"titulo": tit, "fuente": fuente,
                        "fecha": str(date.today()), "nicho": ""})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def economia_hoy(limit=5):
    """Noticias economicas del dia (Google News search, gratis)."""
    out = _news_search("economia+dolar+inflacion+tasas", "GoogleNews-Eco", limit)
    for t in out:
        t["nicho"] = "economia"
    return out


def finanzas_hoy(limit=5):
    out = _news_search("dolar+bitcoin+acciones+mercado+inversion", "GoogleNews-Fin", limit)
    for t in out:
        t["nicho"] = "finanzas"
    return out


def ia_hoy(limit=5):
    out = _news_search("inteligencia+artificial+OpenAI+Google+tecnologia", "GoogleNews-IA", limit)
    for t in out:
        t["nicho"] = "ia_tech"
    return out


def anime_trending(limit=5):
    """Animes en emision mas populares (AniList, gratis). Solo datos, sin footage con copyright."""
    out = []
    try:
        q = {"query": "query { Page(page:1, perPage:12) { media(type:ANIME, status:RELEASING, sort:TRENDING_DESC) { title { romaji english } averageScore genres seasonYear episodes } } }"}
        r = requests.post("https://graphql.anilist.co", json=q, timeout=20)
        for m in r.json()["data"]["Page"]["media"]:
            tit = m["title"].get("english") or m["title"].get("romaji", "?")
            if len(tit) < 3:
                continue
            gen = ", ".join((m.get("genres") or [])[:3])
            hechos = f"Anime en emision ({m.get('seasonYear', '')}). Generos: {gen}. Puntaje: {m.get('averageScore', '?')}/100."
            out.append({"titulo": f"Resena sin spoilers: {tit}", "fuente": "AniList",
                        "fecha": str(date.today()), "hechos": hechos, "nicho": "anime"})
    except Exception:
        pass
    return out[:limit]


def get_tendencias(nicho="curiosidades", limit=5):
    """Devuelve lista de ideas virales según nicho."""
    tendencias = []
    tendencias += google_trends_es(limit=3)
    if nicho == "noticias":
        tendencias += google_news(limit=10)
    elif nicho == "gaming":
        tendencias += reddit_viral(limit=10)
    elif nicho == "futbol":
        return futbol_hoy(limit=limit)
    elif nicho == "anime":
        tendencias += anime_trending(limit=10)
    elif nicho == "economia":
        tendencias += economia_hoy(limit=10)
    elif nicho == "finanzas":
        tendencias += finanzas_hoy(limit=10)
    elif nicho == "ia_tech":
        tendencias += ia_hoy(limit=10)
    else:
        tendencias += reddit_viral(limit=5)

    # Mezclar con evergreen para no depender 100% de internet
    for t in EVERGREEN.get(nicho, []):
        tendencias.append({"titulo": t, "fuente": "evergreen-viral", "fecha": str(datetime.now().date())})

    random.shuffle(tendencias)
    # dedup por titulo + filtrar temas muy cortos (ej "profesor")
    vistos, out = set(), []
    for t in tendencias:
        tit = t["titulo"].strip()
        if len(tit) < 20:
            continue
        if tit not in vistos:
            vistos.add(tit)
            out.append(t)
        if len(out) >= limit:
            break
    # fallback a evergreen si todo fue filtrado
    if not out:
        for t in EVERGREEN.get(nicho, [])[:limit]:
            out.append({"titulo": t, "fuente": "evergreen-viral", "fecha": str(datetime.now().date())})
    return out

if __name__ == "__main__":
    import json
    print(json.dumps(get_tendencias("curiosidades", 5), indent=2, ensure_ascii=False))
