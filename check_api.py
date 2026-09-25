"""Verifica que la API de YouTube esté lista para subir."""
import os, json

print("=== CHECK API YOUTUBE ===")
ok = True

if os.path.exists("client_secrets.json"):
    print("OK  client_secrets.json encontrado")
    try:
        d = json.load(open("client_secrets.json", encoding="utf-8"))
        print("    tipo:", list(d.keys()))
    except Exception as e:
        print("FALLO client_secrets.json corrupto:", e); ok = False
else:
    print("FALTA client_secrets.json -> sigue la guia CONECTAR_YOUTUBE.txt paso 1-3")
    ok = False

if os.path.exists("token_v2.pickle") or os.path.exists("token.pickle"):
    print("OK  token existe (cuenta enlazada)")
    if not os.path.exists("token_v2.pickle"):
        print("AVISO: borra token.pickle y re-autoriza para activar estadisticas (scope readonly)")
else:
    print("PENDIENTE token no existe -> se crea solo al autorizar la primera vez")

try:
    import googleapiclient, google_auth_oauthlib, edge_tts, moviepy, PIL, feedparser
    print("OK  dependencias instaladas")
except Exception as e:
    print("FALTA dependencia:", e); ok = False

print()
print("RESULTADO:", "LISTO PARA SUBIR" if (ok and (os.path.exists("token_v2.pickle") or os.path.exists("token.pickle"))) else "FALTA CONFIGURAR (ver CONECTAR_YOUTUBE.txt)")
