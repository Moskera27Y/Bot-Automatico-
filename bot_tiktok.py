"""Cross-post a TikTok (Content Posting API).
Modos: draft (borrador al inbox, sin auditoria) o direct (publica, exige app auditada).
Setup en CONECTAR_TIKTOK.txt
"""
import json
import os
import time

import requests

BASE = "https://open.tiktokapis.com"
TOKEN_FILE = "tiktok_token.json"


def _cred():
    return (os.getenv("TIKTOK_CLIENT_KEY", ""), os.getenv("TIKTOK_CLIENT_SECRET", ""))


def auth_url(state="kalador"):
    key, _ = _cred()
    red = os.getenv("TIKTOK_REDIRECT", "http://localhost:8081/callback")
    scopes = "user.info.basic,video.upload,video.publish"
    return (f"https://www.tiktok.com/v2/auth/authorize/?client_key={key}&scope={scopes}"
            f"&response_type=code&redirect_uri={red}&state={state}")


def autorizar_con_codigo(code):
    """El usuario autoriza en el navegador y pega el ?code=. Guarda token."""
    key, sec = _cred()
    red = os.getenv("TIKTOK_REDIRECT", "http://localhost:8081/callback")
    r = requests.post(f"{BASE}/v2/oauth/token/", data={
        "client_key": key, "client_secret": sec, "code": code,
        "grant_type": "authorization_code", "redirect_uri": red}, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get("error", {}).get("code") != "ok":
        raise RuntimeError(d)
    tok = {"access_token": d["access_token"], "refresh_token": d.get("refresh_token", ""),
           "open_id": d.get("open_id", ""),
           "expira": time.time() + int(d.get("expires_in", 86400)) - 300}
    json.dump(tok, open(TOKEN_FILE, "w"))
    print("TikTok autorizado.")
    return tok


def _token():
    tok = json.load(open(TOKEN_FILE, encoding="utf-8"))
    if tok["expira"] < time.time() + 60:
        key, sec = _cred()
        r = requests.post(f"{BASE}/v2/oauth/token/", data={
            "client_key": key, "client_secret": sec,
            "grant_type": "refresh_token", "refresh_token": tok["refresh_token"]}, timeout=30)
        r.raise_for_status()
        d = r.json()
        tok.update({"access_token": d["access_token"],
                    "refresh_token": d.get("refresh_token", tok["refresh_token"]),
                    "expira": time.time() + int(d.get("expires_in", 86400)) - 300})
        json.dump(tok, open(TOKEN_FILE, "w"))
    return tok


def subir_tiktok(mp4, titulo, modo="draft"):
    """modo draft: inbox (el usuario lo publica desde la app).
    modo direct: publica ya (exige app auditada; si no, queda privado)."""
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError("TikTok sin autorizar: ejecuta 'python bot_tiktok.py auth'")
    tok = _token()
    head = {"Authorization": f"Bearer {tok['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"}
    size = os.path.getsize(mp4)
    if modo == "direct":
        body = {"post_info": {"title": titulo[:150], "privacy_level": "PUBLIC_TO_EVERYONE"},
                "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                "chunk_size": size, "total_chunk_count": 1},
                "post_mode": "DIRECT_POST", "media_type": "VIDEO"}
        url = f"{BASE}/v2/post/publish/content/init/"
        # averiguar niveles permitidos
        try:
            ci = requests.post(f"{BASE}/v2/post/publish/creator_info/query/",
                               headers=head, json={}, timeout=30).json()
            opts = ci.get("data", {}).get("privacy_level_options", [])
            if opts and "PUBLIC_TO_EVERYONE" not in opts:
                body["post_info"]["privacy_level"] = opts[0]
        except Exception:
            pass
    else:
        body = {"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                "chunk_size": size, "total_chunk_count": 1}}
        url = f"{BASE}/v2/post/publish/inbox/video/init/"
    r = requests.post(url, headers=head, json=body, timeout=60)
    r.raise_for_status()
    d = r.json()
    if d.get("error", {}).get("code") != "ok":
        raise RuntimeError(d)
    pub, up = d["data"]["publish_id"], d["data"]["upload_url"]
    with open(mp4, "rb") as f:
        u = requests.put(up, headers={"Content-Type": "video/mp4",
                                      "Content-Length": str(size),
                                      "Content-Range": f"bytes 0-{size - 1}/{size}"},
                         data=f, timeout=300)
        u.raise_for_status()
    print(f"TikTok {modo}: publish_id {pub}")
    return pub


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        print("1) Abre esta URL y autoriza:\n" + auth_url())
        code = input("2) Pega el ?code= de la URL de retorno: ").strip()
        if "code=" in code:
            import re
            code = re.search(r"code=([^&]+)", code).group(1)
        autorizar_con_codigo(code)
    else:
        print("Uso: python bot_tiktok.py auth")
