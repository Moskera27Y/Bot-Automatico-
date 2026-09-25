"""Stats del canal via YouTube Data API (necesita scope youtube.readonly)."""
from bot_upload import get_youtube


def stats_videos(ids):
    """{video_id: {views, likes, comments, titulo}}"""
    out = {}
    ids = [i for i in ids if i]
    for k in range(0, len(ids), 50):
        yt = get_youtube()
        r = yt.videos().list(id=",".join(ids[k:k + 50]),
                             part="statistics,snippet").execute()
        for it in r.get("items", []):
            s = it.get("statistics", {})
            out[it["id"]] = {"views": int(s.get("viewCount", 0)),
                             "likes": int(s.get("likeCount", 0)),
                             "comments": int(s.get("commentCount", 0)),
                             "titulo": it["snippet"]["title"][:60]}
    return out


def refrescar(cfg, estado, n=20):
    """Actualiza estado['stats'] con los ultimos n videos + top nichos."""
    try:
        ids = [h["yt"] for h in estado.get("historial", []) if h.get("yt")][-n:]
        if not ids:
            return estado
        from datetime import date
        st = stats_videos(ids)
        estado["stats"] = st
        estado["stats_fecha"] = date.today().isoformat()
        por_nicho = {}
        for h in estado.get("historial", []):
            if h.get("yt") in st:
                por_nicho.setdefault(h.get("nicho", "?"), []).append(st[h["yt"]]["views"])
        top = sorted(((sum(v) / len(v), k) for k, v in por_nicho.items()), reverse=True)
        estado["top_nichos"] = [k for _, k in top]
        tot = sum(v["views"] for v in st.values())
        print(f"Stats: {len(st)} videos, {tot} vistas. Top: {estado['top_nichos'][:3]}")
        return estado
    except Exception as e:
        print(f"Stats fallo ({e}) — ¿falta re-autorizar con scope readonly?")
        return estado
