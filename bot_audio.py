"""Cama musical + acentos SFX (assets locales libres: ende.app CC-BY + Kenney CC0)."""
import glob
import os
import subprocess
from datetime import date

MUSICA = sorted(glob.glob("musica/*.mp3"))
SFX_CUTS = sorted(glob.glob("sfx/impactSoft_medium_*.ogg"))
SFX_HOOK = "sfx/bong_001.ogg" if os.path.exists("sfx/bong_001.ogg") else None


def elegir_musica(nicho=""):
    if not MUSICA:
        return None
    idx = (date.today().toordinal() + sum(map(ord, nicho))) % len(MUSICA)
    return MUSICA[idx]


def mezclar(voz_mp3, dur, dest, cortes=None, nicho="", con_musica=True, con_sfx=True):
    """Mezcla voz (-14 LUFS) + musica baja + thumps en cortes. Devuelve dest."""
    cortes = [c for c in (cortes or []) if 0.3 < c < dur - 0.5][:10]
    musica = elegir_musica(nicho) if con_musica else None
    if not musica:
        # sin musica: solo normalizar voz
        subprocess.run(
            ["ffmpeg", "-y", "-i", voz_mp3, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
             "-codec:a", "libmp3lame", "-q:a", "3", dest],
            check=True, capture_output=True)
        return dest
    # cama: musica en loop baja + sfx en cada corte
    inputs = ["-stream_loop", "-1", "-i", musica]
    filtros = ["[0:a]volume=0.14,atrim=0:{:.2f}[bed]".format(dur)]
    idx = 1
    mapa = ["[bed]"]
    if con_sfx:
        if SFX_HOOK:
            inputs += ["-i", SFX_HOOK]
            filtros.append(f"[{idx}:a]adelay=delays=100,volume=0.6[hook]")
            mapa.append("[hook]")
            idx += 1
        if SFX_CUTS and os.path.exists(SFX_CUTS[0]):
            for j, c in enumerate(cortes):
                sfx = SFX_CUTS[j % len(SFX_CUTS)]
                inputs += ["-i", sfx]
                filtros.append(f"[{idx}:a]adelay=delays={int(c * 1000)},volume=0.5[s{idx}]")
                mapa.append(f"[s{idx}]")
                idx += 1
    filtros.append("".join(mapa) + f"amix=inputs={len(mapa)}:normalize=0[bedmix]")
    bed = "temp_frames/bed.mp3"
    subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", ";".join(filtros), "-map", "[bedmix]",
                    "-t", f"{dur:.2f}", bed],
                   check=True, capture_output=True)
    # voz al frente + cama debajo + norm final
    subprocess.run(
        ["ffmpeg", "-y", "-i", voz_mp3, "-i", bed,
         "-filter_complex", "[1:a]volume=0.5[low];[0:a][low]amix=inputs=2:normalize=0,"
                            "loudnorm=I=-14:TP=-1.0:LRA=11",
         "-codec:a", "libmp3lame", "-q:a", "3", "-t", f"{dur:.2f}", dest],
        check=True, capture_output=True)
    print(f"Audio: musica {os.path.basename(musica)} + {len(cortes)} sfx")
    return dest
