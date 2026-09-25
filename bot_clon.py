"""Clonacion de voz local y gratis: Chatterbox Multilingual (MIT, espanol).
Ref: voz_referencia.wav (tu voz, 30-120s limpios, sin musica).
"""
import os
import re
import subprocess

import numpy as np
import soundfile as sf
import torch

REF = "voz_referencia.wav"
SR = 24000
_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        # La marca de agua Perth falla empaquetada (PyInstaller) y es inaudible:
        # se sustituye por no-op antes de cargar el modelo.
        import perth

        class _SinMarca:
            def __init__(self, *a, **k):
                pass

            def apply_watermark(self, wav, sample_rate=None):
                return wav

        perth.PerthImplicitWatermarker = _SinMarca
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Clon: cargando Chatterbox ({device}, primera vez descarga ~2GB)...")
        _MODEL = ChatterboxMultilingualTTS.from_pretrained(device=device)
    return _MODEL


def _trozos(texto, max_chars=280):
    partes = re.split(r"(?<=[.!?])\s+", texto.strip())
    trozos, cur = [], ""
    for p in partes:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                trozos.append(cur)
            cur = p
    if cur:
        trozos.append(cur)
    return trozos or [texto]


def clonar_voz(texto, salida_mp3, ref=REF, language_id="es"):
    if not os.path.exists(ref):
        raise RuntimeError(f"falta {ref}: graba 1-2 min de tu voz (ver GRABAR_VOZ.txt)")
    model = _get_model()
    audios = []
    for t in _trozos(texto):
        wav = model.generate(t, audio_prompt_path=ref, language_id=language_id)
        audios.append(wav.squeeze(0).cpu().numpy())
        audios.append(np.zeros(int(SR * 0.15), dtype=np.float32))
    full = np.concatenate(audios)
    tmp = salida_mp3 + ".clon.wav"
    sf.write(tmp, full, SR)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp, "-codec:a", "libmp3lame", "-q:a", "3", salida_mp3],
        check=True, capture_output=True,
    )
    os.remove(tmp)
    return salida_mp3
