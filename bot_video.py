"""Short 1080x1920: multi-clip Pexels + karaoke + audio -14LUFS + marca minima."""
import json
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from bot_fondos import buscar_fondo, buscar_fondos

W, H = 1080, 1920


def _font(size=60):
    path = "C:/Windows/Fonts/arialbd.ttf"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _tiempos_palabras(guion, dur, words_path=None, recorte=0.0):
    """Lista [{t0,t1,w}] con timings reales (Edge) o estimados (otras voces).
    recorte: segundos eliminados del inicio del audio (se restan)."""
    if words_path and os.path.exists(words_path):
        try:
            data = json.load(open(words_path, encoding="utf-8"))
            if len(data) > 5:
                out = []
                for x in data:
                    t0 = max(0.05, x["t0"] - recorte)
                    t1 = max(t0 + 0.1, x["t1"] - recorte)
                    out.append({"t0": t0, "t1": t1, "w": x["w"]})
                return out
        except Exception:
            pass
    ws = guion.split()
    t0, t1 = 0.1, max(0.4, dur - 0.2)
    per = (t1 - t0) / max(1, len(ws))
    return [{"t0": t0 + i * per, "t1": t0 + (i + 1) * per, "w": w} for i, w in enumerate(ws)]


def _karaoke_png(ventana, activa, dest, size=62, sub=None, prog=0.0):
    """PNG estilo Hormozi: activa con pop (mas grande, dorada) + barra progreso + linea ES."""
    img = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bw = int(940 * max(0.0, min(1.0, prog)))
    d.rectangle([(W - 940) // 2, 14, (W - 940) // 2 + 940, 24], fill=(255, 255, 255, 70))
    d.rectangle([(W - 940) // 2, 14, (W - 940) // 2 + bw, 24], fill=(255, 200, 0))
    fonts = [_font(size + 16) if i == activa else _font(size) for i in range(len(ventana))]
    anchos = []
    for i, w in enumerate(ventana):
        bb = d.textbbox((0, 0), w.upper(), font=fonts[i], stroke_width=2)
        anchos.append(bb[2] - bb[0])
    total = sum(anchos) + 28 * (len(ventana) - 1)
    # auto-ajuste: si desborda 940px, encoger hasta que quepa
    while total > 940 and size > 38:
        size -= 4
        fonts = [_font(size + 12) if i == activa else _font(size) for i in range(len(ventana))]
        anchos = []
        for i, w in enumerate(ventana):
            bb = d.textbbox((0, 0), w.upper(), font=fonts[i], stroke_width=2)
            anchos.append(bb[2] - bb[0])
        total = sum(anchos) + 28 * (len(ventana) - 1)
    x = (W - total) // 2
    for i, w in enumerate(ventana):
        color = (255, 200, 0) if i == activa else (255, 255, 255)
        d.text((x, 60 if i == activa else 68), w.upper(), font=fonts[i], fill=color,
               stroke_width=3, stroke_fill="black")
        x += anchos[i] + 28
    if sub:
        fs = _font(40)
        palabras, lineas, cur = sub.split(), [], ""
        for p in palabras:
            test = (cur + " " + p).strip()
            if len(test) > 28:
                lineas.append(cur)
                cur = p
            else:
                cur = test
        if cur:
            lineas.append(cur)
        y2 = 190
        for ln in lineas[:2]:
            s = ln.upper()
            bb = d.textbbox((0, 0), s, font=fs)
            d.text(((W - (bb[2] - bb[0])) // 2, y2), s, font=fs, fill=(255, 225, 130),
                   stroke_width=2, stroke_fill="black")
            y2 += 56
    img.save(dest)


def _mapa_oraciones(guion_en, guion_es):
    """Por cada palabra EN -> oracion ES correspondiente (alineadas por orden)."""
    import re as _re
    sents_en = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", guion_en.strip()) if s.strip()]
    sents_es = [s.strip() for s in (guion_es or "").split("|") if s.strip()]
    if not sents_es:
        return {}
    counts = [len(s.split()) for s in sents_en]
    n_words = sum(counts) or 1
    return {i: sents_es[min(len(sents_es) - 1, int(i / n_words * len(sents_es)))]
            for i in range(n_words)}


def _marca_agua(dest):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = _font(34)
    bb = d.textbbox((0, 0), "KALADOR", font=f)
    d.text((W - (bb[2] - bb[0]) - 44, H - 120), "KALADOR", font=f, fill=(255, 255, 255, 110))
    img.save(dest)


def _preparar_fondo(src, dur, dest):
    from moviepy import VideoFileClip

    probe = VideoFileClip(src)
    src_dur = probe.duration or 5
    probe.close()
    loops = max(1, math.ceil(dur / src_dur) + 1)
    subprocess.run(
        ["ffmpeg", "-y", "-stream_loop", str(loops), "-i", src,
         "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
         "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-an", dest],
        check=True, capture_output=True,
    )
    return dest


def _cortes_oraciones(words, guion, dur):
    """Tiempos de fin de cada oracion -> cortes de fondo alineados a la narracion."""
    import re as _re
    toks = guion.split()
    cortes, acc = [], 0
    cur = []
    for tok in toks:
        cur.append(tok)
        if _re.search(r"[.!?…]+$", tok):
            acc += len(cur)
            if acc < len(words):
                cortes.append(words[acc - 1]["t1"])
            cur = []
    # fusionar cortes muy juntos, partir tramos largos
    out, prev = [], 0.0
    for c in cortes + [dur]:
        if c - prev < 1.8:
            continue
        while c - prev > 7.0:
            prev += 5.0
            out.append(prev)
        out.append(c)
        prev = c
    return [c for c in out if c < dur - 0.3]


def _preparar_fondo_multi(srcs, dur, dest, foto=None, cortes=None, flash_first=True):
    """Pattern interrupt: foto con zoom fuerte + cortes de ~3.5s rotando clips."""
    from moviepy import VideoFileClip

    if foto and os.path.exists(foto):
        fp = "temp_frames/bgseg_foto.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loop", "1", "-i", foto,
             "-vf", ("scale=1440:2560,zoompan=z='1+0.25*on/84':d=84:"
                     "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24,"
                     "eq=saturation=1.12:contrast=1.04,vignette=PI/5"),
             "-frames:v", "84", "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", "-an", fp],
            check=True, capture_output=True,
        )
        resto = dur - 3.5
        if resto <= 1:
            subprocess.run(["ffmpeg", "-y", "-i", fp, "-t", f"{dur:.2f}",
                            "-c", "copy", dest], check=True, capture_output=True)
            return dest
        sub = "temp_frames/bg_rest.mp4"
        _preparar_fondo_multi(srcs, resto, sub, flash_first=False)
        with open("temp_frames/bglist0.txt", "w") as f:
            f.write(f"file '{os.path.abspath(fp)}'\nfile '{os.path.abspath(sub)}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp_frames/bglist0.txt",
             "-c", "copy", dest],
            check=True, capture_output=True,
        )
        return dest
    durs = []
    for s in srcs:
        try:
            p = VideoFileClip(s)
            durs.append(p.duration or 5)
            p.close()
        except Exception:
            durs.append(5)
    segs, t, i = [], 0.0, 0
    bounds = list(cortes or []) + [dur]
    bi = 0
    while t < dur - 0.05:
        src, sd = srcs[i % len(srcs)], durs[i % len(srcs)]
        # corte en fin de oracion si cae dentro de la ventana util
        lim = min(dur - t, 7.0)
        seg = lim
        while bi < len(bounds) and bounds[bi] <= t + 0.3:
            bi += 1
        if bi < len(bounds) and bounds[bi] - t >= 1.8 and bounds[bi] - t <= 7.0:
            seg = bounds[bi] - t
            bi += 1
        else:
            seg = min(3.0, dur - t)
        start = ((i * 7.3) % max(0.1, sd - seg)) if sd > seg else 0
        frames = max(12, int(seg * 24))
        # punch-in alternado 1.0/1.06 + flash hook en el primer corte
        if i == 0 and flash_first:
            base, amp = 1.0, 0.25
        else:
            base, amp = (1.0, 0.15) if i % 2 == 0 else (1.06, 0.10)
        vf = (f"scale=1440:2560,zoompan=z='{base}+{amp}*on/{frames}':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24,"
              f"eq=saturation=1.12:contrast=1.04,vignette=PI/5")
        fp = f"temp_frames/bgseg_{i}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{start:.2f}", "-i", src,
             "-vf", vf,
             "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", "-an", fp],
            check=True, capture_output=True,
        )
        segs.append(fp)
        t += seg
        i += 1
    with open("temp_frames/bglist.txt", "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp_frames/bglist.txt",
         "-c", "copy", dest],
        check=True, capture_output=True,
    )
    return dest


def _pulir_audio(mp3, dur_max=58):
    """Hook inmediato + nivel parejo: recorta silencio inicial y normaliza a -14 LUFS.
    Devuelve (path_pulido, nueva_dur, recorte_seg)."""
    from moviepy import AudioFileClip

    orig = AudioFileClip(mp3).duration
    dur = min(orig, dur_max)
    leading = 0.0
    try:
        r = subprocess.run(
            ["ffmpeg", "-i", mp3, "-af", "silencedetect=noise=-40dB:d=0.15",
             "-f", "null", "-"],
            capture_output=True, text=True)
        m0 = re.search(r"silence_start:\s*([\d.]+)", r.stderr)
        m1 = re.search(r"silence_end:\s*([\d.]+)", r.stderr)
        if m0 and m1 and float(m0.group(1)) < 0.05:
            leading = min(float(m1.group(1)), 1.5)
    except Exception:
        pass
    dest = "temp_frames/voz_ok.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{leading:.2f}", "-i", mp3,
         "-af", "afade=t=in:st=0:d=0.015,loudnorm=I=-14:TP=-1.0:LRA=11",
         "-t", f"{dur - leading:.2f}", "-codec:a", "libmp3lame", "-q:a", "3", dest],
        check=True, capture_output=True,
    )
    print(f"Audio: recorte {leading:.2f}s + loudnorm -14 LUFS")
    return dest, dur - leading, leading


def _fondo_degradado(dur, dest):
    import imageio_ffmpeg  # noqa: F401  (asegura ffmpeg disponible)
    from moviepy import ImageClip

    yy = np.linspace(0, 1, H)[:, None]
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    arr[:, :, 0] = (12 + 40 * yy).astype(np.uint8)
    arr[:, :, 2] = (45 + 110 * yy).astype(np.uint8)
    ImageClip(arr, duration=dur).write_videofile(
        dest, fps=24, codec="libx264", audio=False,
        preset="veryfast", logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    return dest


def crear_shorts(audio_mp3, guion, salida_mp4, tema="", nicho="curiosidades", words_path=None,
                 tarjeta_path=None, minibug_path=None, sub_y=620, lang="es", guion_es="", foto_path=None,
                 fondos_queries=None):
    from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, ImageClip, VideoFileClip

    audio = AudioFileClip(audio_mp3)
    os.makedirs("temp_frames", exist_ok=True)
    voz_ok, dur, recorte = _pulir_audio(audio_mp3)
    audio.close()
    audio = AudioFileClip(voz_ok)

    fondos = buscar_fondos(tema or guion[:60], nicho, n=3, queries=fondos_queries)
    words = _tiempos_palabras(guion, dur, words_path, recorte=recorte)
    cortes = _cortes_oraciones(words, guion, dur)
    # mezcla final: voz + cama musical + sfx en cortes (misma linea de tiempo)
    from bot_audio import mezclar
    mix = "temp_frames/mix.mp3"
    try:
        mezclar(voz_ok, dur, mix, cortes=cortes, nicho=nicho)
        audio.close()
        audio = AudioFileClip(mix)
    except Exception as e:
        print(f"Aviso mezcla ({e}) -> solo voz")
    bg_path = "temp_frames/bg.mp4"
    try:
        if len(fondos) >= 2:
            _preparar_fondo_multi(fondos, dur, bg_path, foto=foto_path, cortes=cortes)
        elif len(fondos) == 1:
            _preparar_fondo(fondos[0], dur, bg_path)
        else:
            _fondo_degradado(dur, bg_path)
    except Exception as e:
        print(f"Aviso fondo ({e}) -> degradado")
        _fondo_degradado(dur, bg_path)

    clips = [VideoFileClip(bg_path)]
    clips.append(ColorClip(size=(W, H), color=(0, 0, 0)).with_opacity(0.30).with_duration(dur))

    mapa_es = _mapa_oraciones(guion, guion_es) if lang == "en" and guion_es else {}
    # Ventanas de 3 palabras con pop en la activa + linea ES + progreso
    for i, w in enumerate(words):
        g = i // 3
        ventana = [x["w"] for x in words[g * 3:g * 3 + 3]]
        activa = i % 3
        fp = f"temp_frames/kara_{i}.png"
        _karaoke_png(ventana, activa, fp, sub=mapa_es.get(i), prog=(i + 1) / max(1, len(words)))
        t_fin = words[i + 1]["t0"] if i + 1 < len(words) else dur
        clips.append(ImageClip(fp).with_position(("center", sub_y))
                     .with_start(w["t0"]).with_duration(max(0.15, t_fin - w["t0"])))

    if tarjeta_path and os.path.exists(tarjeta_path):
        clips.append(ImageClip(tarjeta_path).with_position(("center", 170))
                     .with_duration(min(4.5, dur)))
    if minibug_path and os.path.exists(minibug_path) and dur > 8:
        clips.append(ImageClip(minibug_path).with_position((40, 200))
                     .with_start(4.0).with_duration(dur - 4.0))

    wm = "temp_frames/wm.png"
    _marca_agua(wm)
    clips.append(ImageClip(wm).with_position((0, 0)).with_duration(dur))

    video = CompositeVideoClip(clips, size=(W, H)).with_audio(audio)
    video.write_videofile(salida_mp4, fps=24, codec="libx264", audio_codec="aac",
                          preset="veryfast", logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"])
    for c in clips:
        c.close()
    audio.close()
    return salida_mp4
