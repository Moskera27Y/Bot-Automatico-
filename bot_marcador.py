"""Tarjeta de marcador con escudos + avatar opcional. Solo texto y logos ESPN."""
from PIL import Image, ImageDraw, ImageFont

from bot_avatar import circulo

DORADO = (255, 200, 0)
W2 = 900


def _font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _centrado(d, y, texto, font, fill, x0=0, x1=W2):
    bb = d.textbbox((0, 0), texto, font=font, stroke_width=1)
    d.text((x0 + (x1 - x0 - (bb[2] - bb[0])) // 2, y), texto, font=font, fill=fill,
           stroke_width=2, stroke_fill="black")


def _ajustar(d, texto, size_ini, max_w):
    size = size_ini
    while size > 20:
        f = _font(size)
        if d.textbbox((0, 0), texto, font=f)[2] <= max_w:
            return f
        size -= 4
    return _font(size)


def build_tarjeta(m, dest, escudo_local=None, escudo_vis=None, avatar=None, avatar_nombre=""):
    """m: {local, vis, gl, gv, goles:[...]}. PNG con escudos y avatar opcional."""
    extra = 250 if avatar else 0
    H2 = 540 + extra
    img = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 6, W2 - 6, H2 - 6], radius=36, fill=(8, 5, 20, 238),
                        outline=DORADO, width=5)
    _centrado(d, 24, "RESULTADO FINAL", _font(38), DORADO)
    if escudo_local and escudo_vis:
        try:
            el = Image.open(escudo_local).convert("RGBA").resize((130, 130))
            ev = Image.open(escudo_vis).convert("RGBA").resize((130, 130))
            img.paste(el, (105, 80), el)
            img.paste(ev, (665, 80), ev)
        except Exception as e:
            print(f"Escudos overlay fallo ({e})")
            escudo_local = None
    if escudo_local and escudo_vis:
        _centrado(d, 92, f"{m['gl']}  -  {m['gv']}", _font(104), DORADO)
        d.text((60, 225), m["local"].upper(), font=_ajustar(d, m["local"].upper(), 44, 360),
               fill="white", stroke_width=2, stroke_fill="black")
        bb = d.textbbox((0, 0), m["vis"].upper(), font=_font(44))
        f2 = _ajustar(d, m["vis"].upper(), 44, 360)
        bb = d.textbbox((0, 0), m["vis"].upper(), font=f2)
        d.text((W2 - 60 - (bb[2] - bb[0]), 225), m["vis"].upper(), font=f2,
               fill="white", stroke_width=2, stroke_fill="black")
        y = 300
    else:
        _centrado(d, 84, m["local"].upper(), _ajustar(d, m["local"].upper(), 54, 800), "white")
        _centrado(d, 156, f"{m['gl']}  -  {m['gv']}", _font(100), DORADO)
        _centrado(d, 286, m["vis"].upper(), _ajustar(d, m["vis"].upper(), 54, 800), "white")
        y = 362
    for g in (m.get("goles") or [])[:3]:
        _centrado(d, y, f"GOLES: {g}" if g == (m.get("goles") or [""])[0] else g,
                  _font(29), (220, 220, 220))
        y += 42
    if avatar:
        try:
            av = circulo(avatar, 150)
            img.paste(av, ((W2 - 150) // 2, H2 - 245), av)
            if avatar_nombre:
                _centrado(d, H2 - 80, avatar_nombre.upper(), _font(30), DORADO)
        except Exception as e:
            print(f"Avatar overlay fallo ({e})")
    img.save(dest)
    return dest


def build_minibug(m, dest):
    """Mini score-bug persistente (460x130): escudos + marcador."""
    from bot_avatar import escudo as _esc
    W3, H3 = 460, 130
    img = Image.new("RGBA", (W3, H3), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W3 - 1, H3 - 1], radius=28, fill=(8, 5, 20, 220),
                        outline=DORADO, width=3)
    try:
        el = Image.open(_esc(m.get("id_local"), m.get("logo_local"))).convert("RGBA").resize((84, 84))
        ev = Image.open(_esc(m.get("id_vis"), m.get("logo_vis"))).convert("RGBA").resize((84, 84))
        img.paste(el, (18, 23), el)
        img.paste(ev, (358, 23), ev)
    except Exception:
        pass
    txt = f"{m['gl']}-{m['gv']}"
    f = _font(64)
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((W3 - (bb[2] - bb[0])) // 2, 28), txt, font=f, fill=DORADO,
           stroke_width=2, stroke_fill="black")
    img.save(dest)
    return dest


def build_figura(nombre, avatar_path, subtitulo, dest):
    """Mini-tarjeta para persona (economia/noticias): avatar + nombre + tema."""
    H2 = 400
    img = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 6, W2 - 6, H2 - 6], radius=36, fill=(8, 5, 20, 238),
                        outline=DORADO, width=5)
    try:
        av = circulo(avatar_path, 220)
        img.paste(av, (60, 90), av)
    except Exception:
        pass
    d.text((330, 110), nombre.upper(), font=_ajustar(d, nombre.upper(), 52, 510),
           fill=DORADO, stroke_width=2, stroke_fill="black")
    # subtitulo con corte simple
    f = _font(34)
    palabras, lineas, cur = subtitulo.split(), [], ""
    for p in palabras:
        if len((cur + " " + p).strip()) > 30:
            lineas.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        lineas.append(cur)
    y = 190
    for ln in lineas[:3]:
        d.text((330, y), ln, font=f, fill="white", stroke_width=2, stroke_fill="black")
        y += 52
    img.save(dest)
    return dest
