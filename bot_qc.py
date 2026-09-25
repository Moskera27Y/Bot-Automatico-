"""Control de calidad post-render (idea de faceless-video-pipeline/qc.py)."""
import json
import os
import subprocess


def qc_video(path, min_dur=10):
    """Verifica streams + duracion + tamaño. Devuelve (ok, motivo)."""
    if not os.path.exists(path) or os.path.getsize(path) < 50_000:
        return False, "archivo inexistente o diminuto"
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_entries",
             "format=duration", "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        info = json.loads(r.stdout)
        streams = info.get("streams", [])
        has_v = any(s.get("codec_type") == "video" for s in streams)
        has_a = any(s.get("codec_type") == "audio" for s in streams)
        if not has_v:
            return False, "sin stream de video"
        if not has_a:
            return False, "sin stream de audio"
        v = next(s for s in streams if s.get("codec_type") == "video")
        if v.get("width", 0) != 1080 or v.get("height", 0) != 1920:
            return False, f"resolucion {v.get('width')}x{v.get('height')}"
        dur = float(info.get("format", {}).get("duration", 0))
        if dur < min_dur:
            return False, f"duracion {dur:.1f}s < {min_dur}s"
        return True, f"OK {dur:.1f}s 1080x1920 A+V"
    except Exception as e:
        return False, f"ffprobe fallo: {e}"
