"""Genera logo de perfil KALADOR (800x800, apto recorte circular YouTube)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = 800
DORADO = (255, 200, 0)
DORADO_OSCURO = (160, 110, 0)

def font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()

# Fondo negro-violeta con resplandor central
yy, xx = np.mgrid[0:S, 0:S]
t = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
glow = np.exp(-((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (2 * 300.0 ** 2))
r = np.clip(8 + glow * 60, 0, 255)
g = np.clip(5 + glow * 30, 0, 255)
b = np.clip(20 + glow * 100 + (1 - np.clip(t, 0, 1)) * 10, 0, 255)
img = Image.fromarray(np.stack([r, g, b], -1).astype(np.uint8))
d = ImageDraw.Draw(img)

# Anillo dorado (margen seguro para recorte circular)
d.ellipse([34, 34, S - 34, S - 34], outline=DORADO, width=10)
d.ellipse([58, 58, S - 58, S - 58], outline=DORADO_OSCURO, width=3)

# Letra K gigante con sombra de profundidad
f_k = font(430)
for dx, dy, col in [(0, 14, DORADO_OSCURO), (0, 0, DORADO)]:
    bbox = d.textbbox((0, 0), "K", font=f_k)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((S - tw) / 2 - bbox[0] + dx, 130 + dy), "K", font=f_k, fill=col)

# Nombre debajo
f_n = font(72)
bbox = d.textbbox((0, 0), "KALADOR", font=f_n)
tw = bbox[2] - bbox[0]
d.text(((S - tw) / 2, 590), "KALADOR", font=f_n, fill=DORADO)

img.save("logo_kalador.png")
print("OK logo_kalador.png 800x800")
