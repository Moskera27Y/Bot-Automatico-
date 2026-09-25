"""Aviso por WhatsApp via Hermes Agent Gateway (hermes send)."""
import subprocess

DESTINO_DEFAULT = "whatsapp:573185171163"


def notificar(texto, destino=None):
    tgt = destino or DESTINO_DEFAULT
    try:
        r = subprocess.run(
            ["hermes", "send", "--to", tgt, texto],
            capture_output=True, text=True, timeout=120,
        )
        ok = r.returncode == 0
        print("WPP:", "enviado" if ok else f"FALLO {(r.stderr or r.stdout)[:200]}")
        return ok
    except Exception as e:
        print("WPP fallo:", e)
        return False


if __name__ == "__main__":
    notificar("KALADOR bot: notificaciones activadas. Te avisare de cada video publicado.")
