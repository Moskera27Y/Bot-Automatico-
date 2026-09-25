"""Subida a YouTube Shorts con YouTube Data API v3."""
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
TOKEN = "token_v2.pickle"


class QuotaAgotada(Exception):
    pass

def get_youtube(client_secrets="client_secrets.json"):
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets):
                raise FileNotFoundError(
                    f"No encuentro {client_secrets}. Descárgalo de Google Cloud Console > APIs > Credenciales > OAuth Client ID (Escritorio)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)

def subir_shorts(mp4: str, titulo: str, descripcion: str, tags: list, privacy="public", client_secrets="client_secrets.json"):
    yt = get_youtube(client_secrets)
    body = {
        "snippet": {"title": titulo, "description": descripcion, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(mp4, mimetype="video/mp4", resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    try:
        while resp is None:
            status, resp = req.next_chunk()
            if status:
                print(f"Subiendo {int(status.progress()*100)}%...")
    except HttpError as e:
        if e.resp.status == 403 and "quotaExceeded" in str(e.content):
            raise QuotaAgotada("Cuota diaria de YouTube agotada (~6 videos/dia en plan gratis).")
        raise
    print("OK Publicado! ID:", resp["id"], f"https://youtube.com/shorts/{resp['id']}")
    return resp["id"]
