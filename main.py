"""Orquestador: tendencia -> guion -> voz -> video -> upload + aviso WPP."""
import os, json, argparse, random, traceback, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
except Exception:
    pass
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from bot_trends import get_tendencias
from bot_scripts import generar_guion
from bot_voice import texto_a_voz
from bot_video import crear_shorts
from bot_upload import subir_shorts, QuotaAgotada
from bot_notifica import notificar
from bot_marcador import build_tarjeta, build_figura, build_minibug
from bot_avatar import escudo, avatar_persona, foto_partido
from bot_qc import qc_video

# Nichos de evento (sin tope: todo lo nuevo se cubre) vs evergreen (1/dia c/u)
EVENTO = ["futbol", "economia", "noticias"]


def load_config():
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)


def run_un_video(nicho, cfg, subir=True, trend=None, persona=""):
    print(f"\n--- [{nicho}] {datetime.now()} ---")
    trends = get_tendencias(nicho, limit=5)
    t = trend or (trends[0] if trends else None)
    if not t:
        print(f"Sin temas para {nicho}, se omite.")
        return None
    tema = t["titulo"]
    hechos = t.get("hechos", "")
    print("Tema:", tema)
    lang = "en" if nicho in cfg.get("english_nichos", []) else "es"
    series = cfg.get("series", {})
    try:
        n_serie = sum(1 for h in load_estado().get("historial", []) if h.get("nicho") == nicho)
    except Exception:
        n_serie = 0
    serie = series.get(nicho, "") if n_serie % 3 == 2 else ""
    data = generar_guion(tema, nicho, hechos=hechos, lang=lang, serie=serie)
    if data.get("lang") == "es":
        lang = "es"  # fallback plantilla: todo en español
    print("Título:", data["titulo"])

    os.makedirs(cfg["ruta_salida"], exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mp3 = f"{cfg['ruta_salida']}/{nicho}_{stamp}.mp3"
    mp4 = f"{cfg['ruta_salida']}/{nicho}_{stamp}.mp4"

    texto_a_voz(data["guion"], mp3, voz=cfg["voz"], lang=lang, clon_ok=(lang == "es"),
                orden=(cfg.get("orden_voz") or {}).get(lang))
    words = mp3 + ".words.json"
    tarjeta, sub_y, credito, foto, minibug = None, 620, "", None, None

    if nicho == "futbol" and t.get("marcador"):
        m = t["marcador"]
        el = escudo(m.get("id_local"), m.get("logo_local"))
        ev = escudo(m.get("id_vis"), m.get("logo_vis"))
        av, av_nom, cred = None, "", ""
        gl = (m.get("goles") or [""])[0]
        quien = persona or gl.rsplit(" ", 1)[0]
        if quien:
            av, cred = avatar_persona(quien)
            av_nom = quien
            credito = cred
        foto = foto_partido(m.get("local", ""), m.get("vis", ""))
        tarjeta = f"{cfg['ruta_salida']}/{nicho}_{stamp}_tarjeta.png"
        build_tarjeta(m, tarjeta, escudo_local=el, escudo_vis=ev,
                      avatar=av, avatar_nombre=av_nom)
        minibug = f"{cfg['ruta_salida']}/{nicho}_{stamp}_bug.png"
        try:
            build_minibug(m, minibug)
        except Exception as e:
            print(f"Minibug fallo ({e})")
            minibug = None
        sub_y = 1150
    elif persona or data.get("persona"):
        nom = persona or data.get("persona")
        av, cred = avatar_persona(nom)
        credito = cred
        tarjeta = f"{cfg['ruta_salida']}/{nicho}_{stamp}_figura.png"
        build_figura(nom, av, tema[:60], tarjeta)
        sub_y = 1150

    if credito:
        data["descripcion"] += f"\n{credito}"
    data["descripcion"] += "\nMusica: Sascha Ende (ende.app)"
    crear_shorts(mp3, data["guion"], mp4, tema=tema, nicho=nicho,
                 words_path=words if os.path.exists(words) else None,
                 tarjeta_path=tarjeta, minibug_path=minibug, sub_y=sub_y, lang=lang,
                 guion_es=data.get("guion_es", ""), foto_path=foto,
                 fondos_queries=data.get("fondos"))
    ok, motivo = qc_video(mp4)
    print("QC:", motivo)
    if not ok:
        notificar(f"KALADOR: video RECHAZADO por QC ({motivo}): {data['titulo']}",
                  destino=cfg.get("whatsapp"))
        return None
    print("Video creado:", mp4)

    vid = None
    if subir:
        try:
            vid = subir_shorts(mp4, data["titulo"], data["descripcion"], data["tags"],
                               privacy=cfg["upload_privacy"],
                               client_secrets=cfg["ruta_client_secrets"])
            extra = ""
            if os.getenv("TIKTOK_CLIENT_KEY", ""):
                try:
                    from bot_tiktok import subir_tiktok
                    pub = subir_tiktok(mp4, data["titulo"],
                                       modo=cfg.get("tiktok_modo", "draft"))
                    extra = f"\nTikTok {cfg.get('tiktok_modo', 'draft')}: {pub}"
                except Exception as te:
                    extra = f"\nTikTok fallo: {te}"
            notificar(f"KALADOR: video publicado\n{data['titulo']}\nhttps://youtube.com/shorts/{vid}{extra}",
                      destino=cfg.get("whatsapp"))
            registrar_historial(nicho, data["titulo"], mp4, vid)
        except QuotaAgotada as q:
            print(str(q))
            notificar(f"KALADOR: {q} Reanudo manana.", destino=cfg.get("whatsapp"))
            raise
        except Exception as e:
            print("No se pudo subir (¿falta client_secrets.json / token?):", e)
            traceback.print_exc()
    return {"tema": tema, **data, "mp4": mp4, "youtube_id": vid}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", default="todos", help="curiosidades|noticias|gaming|anime|futbol|economia|todos")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--count", type=int, default=0, help="cuántos videos (0=usa config)")
    ap.add_argument("--daemon", action="store_true", help="vigila tendencias todo el dia")
    ap.add_argument("--panel", action="store_true", help="interfaz grafica KALADOR")
    ap.add_argument("--persona", default="", help="persona para avatar (foto libre)")
    args = ap.parse_args()

    cfg = load_config()
    if args.panel:
        from panel_kalador import lanzar
        lanzar(cfg)
        return
    if args.daemon:
        daemon(cfg)
        return
    nichos = cfg["nichos"] if args.niche == "todos" else [args.niche]
    n = args.count or cfg["videos_por_dia"]

    for _ in range(n):
        nicho = random.choice(nichos)
        try:
            run_un_video(nicho, cfg, subir=not args.no_upload, persona=args.persona)
        except QuotaAgotada:
            break


def load_estado():
    try:
        return json.load(open("estado.json", encoding="utf-8"))
    except Exception:
        return {"fecha": "", "cubiertos": [], "evergreen_hoy": {}}


def save_estado(e):
    json.dump(e, open("estado.json", "w", encoding="utf-8"))


def registrar_historial(nicho, titulo, mp4, yt):
    try:
        e = load_estado()
        h = e.get("historial", [])
        h.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "nicho": nicho,
                  "titulo": titulo, "mp4": mp4, "yt": yt})
        e["historial"] = h[-150:]
        save_estado(e)
    except Exception as ex:
        print("Historial fallo:", ex)


def dormir_hasta_manana():
    import time
    from datetime import date, datetime as dt, timedelta
    manana = dt.combine(date.today() + timedelta(days=1), dt.min.time()) + timedelta(minutes=10)
    segs = max(60, int((manana - dt.now()).total_seconds()))
    print(f"Cuota agotada: duermo {segs // 3600}h hasta manana.")
    time.sleep(segs)


def hora_colombia():
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-5))).hour


def daemon(cfg, stop=None):
    """Vigila todo el dia: eventos nuevos siempre + MINIMO min_videos_dia/dia.
    Evergreen 1/dia c/u en horario pico Colombia. Freno real: cuota YT (~6/dia)."""
    import time
    from datetime import date
    intervalo = cfg.get("intervalo_min", 120) * 60
    minimo = cfg.get("min_videos_dia", 3)
    print(f"KALADOR daemon: cada {intervalo // 60} min, minimo {minimo}/dia (freno: cuota YT).")
    while not (stop and stop.is_set()):
        try:
            hoy = date.today().isoformat()
            e = load_estado()
            if e.get("fecha") != hoy:
                e = {"fecha": hoy, "cubiertos": e.get("cubiertos", [])[-300:],
                     "evergreen_hoy": {}, "hechos_hoy": 0}
            e["hechos_hoy"] = e.get("hechos_hoy", sum(
                1 for h in e.get("historial", []) if h.get("fecha", "").startswith(hoy)))
            # stats 1 vez/dia + top nichos para ordenar evergreen
            if e.get("stats_fecha") != hoy and e.get("historial"):
                from bot_stats import refrescar
                e = refrescar(cfg, e)
                save_estado(e)
            # semanal: sabados, una vez por semana ISO
            from datetime import date as _d
            sem = f"{_d.today().isocalendar()[0]}-W{_d.today().isocalendar()[1]}"
            if _d.today().weekday() == 5 and e.get("semanal") != sem:
                try:
                    from bot_semanal import subir_semanal
                    if subir_semanal(cfg):
                        e["semanal"] = sem
                        save_estado(e)
                except QuotaAgotada:
                    save_estado(e)
                    dormir_hasta_manana()
                    continue
                except Exception as ex:
                    print("Semanal fallo:", ex)
            for nicho in EVENTO:
                if stop and stop.is_set():
                    break
                for t in get_tendencias(nicho, limit=5):
                    if t["titulo"] in e["cubiertos"]:
                        continue
                    try:
                        if run_un_video(nicho, cfg, subir=True, trend=t):
                            e["cubiertos"].append(t["titulo"])
                            e["hechos_hoy"] = e.get("hechos_hoy", 0) + 1
                            save_estado(e)
                            time.sleep(300)  # 5 min entre subidas
                    except QuotaAgotada:
                        save_estado(e)
                        dormir_hasta_manana()
                        break
            ordenados = [n for n in cfg["nichos"] if n not in EVENTO]
            top = [n for n in e.get("top_nichos", []) if n in ordenados]
            ordenados = top + [n for n in ordenados if n not in top]
            for nicho in ordenados:
                if stop and stop.is_set():
                    break
                if e["evergreen_hoy"].get(nicho):
                    continue
                h = hora_colombia()
                if not (cfg.get("evergreen_desde", 11) <= h < cfg.get("evergreen_hasta", 23)):
                    continue  # evergreen solo en horario pico Colombia
                cands = [t for t in get_tendencias(nicho, limit=5) if t["titulo"] not in e["cubiertos"]]
                if not cands:
                    continue
                try:
                    if run_un_video(nicho, cfg, subir=True, trend=cands[0]):
                        e["cubiertos"].append(cands[0]["titulo"])
                        e["evergreen_hoy"][nicho] = True
                        e["hechos_hoy"] = e.get("hechos_hoy", 0) + 1
                        save_estado(e)
                        time.sleep(300)
                except QuotaAgotada:
                    save_estado(e)
                    dormir_hasta_manana()
                    break
            # Relleno hasta el minimo diario con lo que haya sin cubrir
            while e.get("hechos_hoy", 0) < minimo:
                if stop and stop.is_set():
                    break
                relleno = None
                for nicho in cfg["nichos"]:
                    cands = [t for t in get_tendencias(nicho, limit=5) if t["titulo"] not in e["cubiertos"]]
                    if cands:
                        relleno = (nicho, cands[0])
                        break
                if not relleno:
                    break
                try:
                    if run_un_video(relleno[0], cfg, subir=True, trend=relleno[1]):
                        e["cubiertos"].append(relleno[1]["titulo"])
                        e["hechos_hoy"] = e.get("hechos_hoy", 0) + 1
                        save_estado(e)
                        time.sleep(300)
                    else:
                        e["cubiertos"].append(relleno[1]["titulo"])
                        save_estado(e)
                except QuotaAgotada:
                    save_estado(e)
                    dormir_hasta_manana()
                    break
            print(f"[{datetime.now()}] Ciclo listo ({e.get('hechos_hoy', 0)} hoy). Duermo {intervalo // 60} min.")
        except Exception as ex:
            print("Daemon error:", ex)
            traceback.print_exc()
        for _ in range(int(intervalo // 10)):
            if stop and stop.is_set():
                return
            time.sleep(10)


if __name__ == "__main__":
    main()
