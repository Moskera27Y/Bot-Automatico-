"""Recopilatorio semanal LARGO (el dinero real): Shorts de 7 dias + intro/outro."""
import glob
import os
import subprocess
from datetime import date, datetime

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920


def _font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _cartel(titulo, sub, dest):
    import numpy as np
    yy = (np.linspace(0, 1, H)[:, None] * 255).astype("uint8")
    arr = np.zeros((H, W, 3), dtype="uint8")
    arr[:, :, 0] = (yy * 0.15).astype("uint8")
    arr[:, :, 2] = (40 + yy * 0.45).astype("uint8")
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 150], fill=(8, 5, 20))
    d.rectangle([0, 150, W, 158], fill=(255, 200, 0))
    f1, f2 = _font(110), _font(54)
    for txt, f, y in [(titulo, f1, 700), (sub, f2, 900)]:
        bb = d.textbbox((0, 0), txt, font=f, stroke_width=2)
        d.text(((W - (bb[2] - bb[0])) // 2, y), txt, font=f, fill="white",
               stroke_width=3, stroke_fill="black")
    img.save(dest)


def _seg_foto(png, dur, dest):
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", png, "-f", "lavfi", "-i",
         "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.1f}", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-preset", "veryfast", "-c:a", "aac",
         "-shortest", dest],
        check=True, capture_output=True)


def _dur(path):
    from moviepy import VideoFileClip
    v = VideoFileClip(path)
    d = v.duration
    v.close()
    return d


def build_semanal(cfg, dias=7, max_min=8):
    os.makedirs("temp_frames", exist_ok=True)
    ahora = datetime.now().timestamp()
    cands = []
    for f in glob.glob(f"{cfg['ruta_salida']}/*.mp4"):
        base = os.path.basename(f)
        if base.startswith("semanal_"):
            continue
        if ahora - os.path.getmtime(f) > dias * 86400:
            continue
        try:
            cands.append((f, _dur(f)))
        except Exception:
            continue
    cands.sort(key=lambda x: os.path.getmtime(x[0]))
    clips, total = [], 0.0
    for f, d in cands:
        if total + d > max_min * 60:
            break
        clips.append(f)
        total += d
    if len(clips) < 2:
        print(f"Semanal: solo {len(clips)} videos, se omite.")
        return None
    _cartel("KALADOR", "LO MEJOR DE LA SEMANA", "temp_frames/sem_in.png")
    _cartel("KALADOR", "MANANA MAS VIDEOS", "temp_frames/sem_out.png")
    _seg_foto("temp_frames/sem_in.png", 3.0, "temp_frames/sem_in.mp4")
    _seg_foto("temp_frames/sem_out.png", 2.5, "temp_frames/sem_out.mp4")
    todos = ["temp_frames/sem_in.mp4"] + clips + ["temp_frames/sem_out.mp4"]
    stamp = date.today().strftime("%Y%m%d")
    dest = f"{cfg['ruta_salida']}/semanal_{stamp}.mp4"
    ins, filt = [], []
    for i, c in enumerate(todos):
        ins += ["-i", c]
        filt.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,setsar=1[v{i}];[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
    filt.append("".join(f"[v{i}][a{i}]" for i in range(len(todos))) +
                f"concat=n={len(todos)}:v=1:a=1[vv][aa]")
    subprocess.run(
        ["ffmpeg", "-y"] + ins + ["-filter_complex", ";".join(filt),
                                  "-map", "[vv]", "-map", "[aa]", "-c:v", "libx264",
                                  "-preset", "veryfast", "-pix_fmt", "yuv420p",
                                  "-c:a", "aac", dest],
        check=True, capture_output=True)
    print(f"Semanal: {len(clips)} clips, {total / 60:.1f} min -> {dest}")
    return dest


def subir_semanal(cfg):
    from bot_notifica import notificar
    from bot_upload import subir_shorts

    mp4 = build_semanal(cfg)
    if not mp4:
        return None
    titulo = f"Lo mejor de la semana en KALADOR | Resumen {date.today().strftime('%d/%m')}"
    desc = ("Recopilacion semanal: noticias, futbol, finanzas, historia y mas.\n\n"
            "Video diario en Shorts.\nMusica: Sascha Ende (ende.app)\n"
            "#resumen #noticias #futbol #finanzas #kalador")
    vid = subir_shorts(mp4, titulo, desc, ["resumen", "noticias", "kalador", "semanales"],
                       privacy=cfg.get("upload_privacy", "public"),
                       client_secrets=cfg.get("ruta_client_secrets", "client_secrets.json"))
    notificar(f"KALADOR: semanal publicado\n{titulo}\nhttps://youtu.be/{vid}",
              destino=cfg.get("whatsapp"))
    return vid
