"""Voz con orden configurable: clon local -> Gemini TTS -> ElevenLabs -> Edge-TTS."""
import asyncio
import json
import os
import subprocess

import edge_tts

VOZ_EN = "en-US-ChristopherNeural"
ORDEN_DEFAULT = {"es": ["clon", "gemini", "edge"], "en": ["gemini", "edge"]}


def _edge(texto, voz, salida, lang="es"):
    async def _gen():
        # rate 0%: +10% sonaba acelerado/robotico. Puntuacion = pausas naturales.
        comm = edge_tts.Communicate(texto, voz, rate="+0%", pitch="+0Hz")
        bounds = []
        with open(salida, "wb") as f:
            async for chunk in comm.stream():
                if chunk.get("type") == "audio":
                    f.write(chunk.get("data", b""))
                elif chunk.get("type") == "WordBoundary":
                    bounds.append({
                        "t0": chunk["offset"] / 10_000_000,
                        "t1": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                        "w": chunk["text"],
                    })
        with open(salida + ".words.json", "w", encoding="utf-8") as f:
            json.dump(bounds, f)

    try:
        asyncio.run(_gen())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_gen())
        loop.close()


def _elevenlabs(texto, salida):
    import requests

    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key:
        raise RuntimeError("sin ELEVENLABS_API_KEY")
    voice = os.getenv("ELEVENLABS_VOICE_ID", "")
    if not voice:
        raise RuntimeError("falta ELEVENLABS_VOICE_ID (clona tu voz en elevenlabs.io > Voices)")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={
            "text": texto,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.75},
        },
        timeout=120,
    )
    r.raise_for_status()
    with open(salida, "wb") as f:
        f.write(r.content)


def _gemini(texto, salida, lang="es"):
    """Gemini TTS gratis (AI Studio, 70+ idiomas, estilo dirigible). Sin timings."""
    import base64
    import wave

    import requests

    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("sin GEMINI_API_KEY (gratis en aistudio.google.com)")
    voice = os.getenv("GEMINI_VOICE_ES" if lang == "es" else "GEMINI_VOICE_EN",
                      "Kore" if lang == "es" else "Puck")
    estilo = ("Narra con energia de presentador viral, ritmo rapido: "
              if lang == "es" else
              "Narrate like an energetic viral host, fast-paced: ")
    model = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": estilo + texto}]}],
              "generationConfig": {
                  "responseModalities": ["AUDIO"],
                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}},
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    tmp = salida + ".gem.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(base64.b64decode(data))
    subprocess.run(["ffmpeg", "-y", "-i", tmp, "-codec:a", "libmp3lame",
                    "-q:a", "3", salida], check=True, capture_output=True)
    os.remove(tmp)


def texto_a_voz(texto, salida_mp3, voz="es-MX-DaliaNeural", lang="es",
                clon_ok=True, orden=None):
    orden = orden or ORDEN_DEFAULT.get(lang, ["gemini", "edge"])
    errores = []
    for prov in orden:
        try:
            if prov == "clon":
                from bot_clon import clonar_voz, REF

                if not clon_ok:
                    raise RuntimeError("clon desactivado para este idioma")
                if not os.path.exists(REF):
                    raise RuntimeError(f"falta {REF}")
                clonar_voz(texto, salida_mp3, language_id=lang)
                print(f"Voz: clon local ({lang})")
                return salida_mp3
            if prov == "gemini":
                _gemini(texto, salida_mp3, lang)
                print(f"Voz: Gemini ({lang})")
                return salida_mp3
            if prov == "elevenlabs":
                _elevenlabs(texto, salida_mp3)
                print("Voz: ElevenLabs")
                return salida_mp3
            if prov == "edge":
                voz_ef = voz if lang == "es" else VOZ_EN
                _edge(texto, voz_ef, salida_mp3, lang)
                print(f"Voz: Edge-TTS ({voz_ef})")
                return salida_mp3
            raise RuntimeError(f"proveedor desconocido: {prov}")
        except Exception as e:
            errores.append(f"{prov}: {e}")
            print(f"Voz {prov} fallo [{e}] -> siguiente")
    print("Voz: todos fallaron:", " | ".join(errores))
    # Ultimo recurso: Edge directo (lanza si falla)
    voz_ef = voz if lang == "es" else VOZ_EN
    _edge(texto, voz_ef, salida_mp3, lang)
    return salida_mp3
