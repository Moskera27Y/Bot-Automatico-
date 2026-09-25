# KALADOR — Fábrica automática de Shorts

Bot en Python que detecta tendencias, escribe guiones con IA, narra con tu voz clonada
(o Gemini/Edge), monta video vertical con metraje stock + karaoke y lo publica en
YouTube Shorts (y TikTok), avisando por WhatsApp.

## Uso rápido
1. `pip install -r requirements.txt` (+ `torch --index-url .../cpu` y `chatterbox` para clonar voz)
2. Copia `.env.example` a `.env` y pon tus keys gratuitas (Groq, Pexels, Gemini)
3. `python main.py --niche todos` · Panel: `python main.py --panel` · 24/7: `python main.py --daemon`
4. Guías: `CONECTAR_YOUTUBE.txt`, `CONECTAR_TIKTOK.txt`, `GRABAR_VOZ.txt`

## Web del proyecto (para verificar dominios)
Carpeta `site/` publicada con GitHub Pages: términos y privacidad.
