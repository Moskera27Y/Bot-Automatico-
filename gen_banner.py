"""Banner YouTube KALADOR 2560x1440 (zona segura 1546x423 centrada)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 2560, 1440
DORADO = (255, 200, 0)
DORADO_OSCURO = (160, 110, 0)

def font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()

yy, xx = np.mgrid[0:H, 0:W]
glow = np.exp(-((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (2 * 700.0 ** 2))
t = yy / H
r = np.clip(8 + 28 * t + glow * 70, 0, 255)
g = np.clip(5 + 16 * t + glow * 28, 0, 255)
b = np.clip(22 + 95 * t + glow * 110, 0, 255)
img = Image.fromarray(np.stack([r, g, b], -1).astype(np.uint8))
d = ImageDraw.Draw(img, "RGBA")

# Sin adornos laterales: solo texto sobre el degradado

# Lineas doradas superior/inferior
d.rectangle([0, 0, W, 14], fill=DORADO)
d.rectangle([0, H - 14, W, H], fill=DORADO)

# Area segura "todos los dispositivos": x 507-2053, y 508-931.
# El texto debe caber en max 1400px de ancho, centrado.
def ajustar(texto, size_ini, max_w):
    size = size_ini
    while size > 20:
        f = font(size)
        bb = d.textbbox((0, 0), texto, font=f)
        if bb[2] - bb[0] <= max_w:
            return f, bb, size
        size -= 6
    f = font(size)
    return f, d.textbbox((0, 0), texto, font=f), size

f_marca, bb, s1 = ajustar("KALADOR", 230, 1400)
tw = bb[2] - bb[0]
d.text(((W - tw) / 2 - bb[0], 540), "KALADOR", font=f_marca, fill=DORADO)

sub = "VIDEO DIARIO  •  DATOS  •  NOTICIAS  •  GAMING"
f_sub, bb2, s2 = ajustar(sub, 72, 1400)
tw2 = bb2[2] - bb2[0]
x2, y2 = (W - tw2) / 2 - bb2[0], 800
d.text((x2, y2), sub, font=f_sub, fill="white")
print(f"marca size={s1} x=[{(W-tw)/2:.0f},{(W+tw)/2:.0f}] | sub size={s2} x=[{x2:.0f},{x2+tw2:.0f}] y=[{y2},{y2+110}]")
print("segura x=[507,2053] y=[508,931] ->",
      "OK" if (W - tw) / 2 >= 507 and (W + tw) / 2 <= 2053 and x2 >= 507 and x2 + tw2 <= 2053 else "FALLO")

img.save("banner_kalador.png")
print("OK banner_kalador.png 2560x1440")
