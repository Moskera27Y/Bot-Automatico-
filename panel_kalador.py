"""Panel KALADOR Pro (CustomTkinter): Crear + Vigilancia + Historial."""
import os
import queue
import threading

import customtkinter as ctk
from PIL import Image

from bot_trends import get_tendencias
from main import daemon, load_estado, run_un_video

FONDO, PANEL, ORO, TEXTO, SUB = "#0b0620", "#150b33", "#ffc800", "#ffffff", "#a79bc9"

ctk.set_appearance_mode("dark")


class LogCola:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s.strip():
            self.q.put((None, s.rstrip()))

    def flush(self):
        pass


def lanzar(cfg):
    q = queue.Queue()
    stop = threading.Event()
    vig = {"t": None}
    trabajando = {"n": 0}

    root = ctk.CTk()
    root.title("KALADOR — Panel Pro")
    root.geometry("760x760")
    root.configure(fg_color=FONDO)

    # ---- cabecera ----
    head = ctk.CTkFrame(root, fg_color="transparent")
    head.pack(fill="x", padx=16, pady=(12, 4))
    try:
        logo_img = ctk.CTkImage(Image.open("logo_kalador.png"), size=(56, 56))
        ctk.CTkLabel(head, image=logo_img, text="").pack(side="left", padx=(0, 10))
    except Exception:
        pass
    ctk.CTkLabel(head, text="KALADOR", font=("Arial", 28, "bold"), text_color=ORO).pack(side="left")
    dot = ctk.CTkLabel(head, text="●", font=("Arial", 22), text_color="#5a5a6e")
    dot.pack(side="right", padx=4)
    estado_lbl = ctk.CTkLabel(head, text="PAUSADO", font=("Arial", 11), text_color=SUB)
    estado_lbl.pack(side="right")

    def pulso(on=True):
        if vig["t"] and vig["t"].is_alive():
            dot.configure(text_color="#3ddc84" if on else "#1a7a4a")
            estado_lbl.configure(text="VIGILANDO")
        else:
            dot.configure(text_color="#5a5a6e")
            estado_lbl.configure(text="PAUSADO")
        root.after(700, pulso, not on)

    # ---- stats ----
    stat_lbl = ctk.CTkLabel(root, text="", font=("Arial", 12), text_color=TEXTO)
    stat_lbl.pack(padx=16, pady=2)

    def refrescar_stats():
        e = load_estado()
        out = cfg.get("ruta_salida", "output")
        mp4s = [f for f in os.listdir(out) if f.endswith(".mp4")] if os.path.exists(out) else []
        stat_lbl.configure(
            text=f"Hoy: {e.get('fecha', '-')} • Hechos: {e.get('hechos_hoy', 0)} • "
                 f"Videos en disco: {len(mp4s)} • Nichos: {len(cfg['nichos'])}")

    # ---- pestañas ----
    tabs = ctk.CTkTabview(root, fg_color=PANEL, segmented_button_fg_color=FONDO,
                          segmented_button_selected_color=ORO,
                          segmented_button_selected_hover_color="#e0a800",
                          segmented_button_unselected_color="#241645",
                          text_color=TEXTO)
    tabs.pack(fill="x", padx=16, pady=6)
    for t in ("Crear", "Vigilancia", "Historial"):
        tabs.add(t)
    tabs.tab("Crear").configure(fg_color=PANEL)
    tabs.tab("Vigilancia").configure(fg_color=PANEL)
    tabs.tab("Historial").configure(fg_color=PANEL)

    # == Crear ==
    fc = tabs.tab("Crear")
    ctk.CTkLabel(fc, text="Nicho", text_color=SUB).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
    ctk.CTkLabel(fc, text="Persona (avatar libre)", text_color=SUB).grid(row=0, column=1, sticky="w", padx=10, pady=(8, 0))
    nicho = ctk.CTkComboBox(fc, values=cfg["nichos"], width=200, fg_color=FONDO,
                            border_color=ORO, button_color=ORO, button_hover_color="#e0a800")
    nicho.set("futbol")
    nicho.grid(row=1, column=0, sticky="w", padx=10)
    persona_var = ctk.StringVar()
    ctk.CTkEntry(fc, textvariable=persona_var, width=220, fg_color=FONDO,
                 border_color="#3a2a6e").grid(row=1, column=1, sticky="w", padx=10)
    ctk.CTkLabel(fc, text="Tema", text_color=SUB).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))
    tema_var = ctk.StringVar()
    ctk.CTkEntry(fc, textvariable=tema_var, width=660, fg_color=FONDO,
                 border_color="#3a2a6e").grid(row=3, column=0, columnspan=2, sticky="we", padx=10)
    ctk.CTkLabel(fc, text="Contexto / datos (el guion los usa tal cual)", text_color=SUB).grid(
        row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))
    ctx = ctk.CTkTextbox(fc, height=70, width=660, fg_color=FONDO, border_color="#3a2a6e")
    ctx.grid(row=5, column=0, columnspan=2, sticky="we", padx=10, pady=(0, 6))
    fb = ctk.CTkFrame(fc, fg_color="transparent")
    fb.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=6)
    prog = ctk.CTkProgressBar(fb, width=180, progress_color=ORO, fg_color="#2a1a55")
    prog.pack(side="right", padx=6)
    prog.set(0)

    # == Vigilancia ==
    fv = tabs.tab("Vigilancia")
    ctk.CTkLabel(fv, text=f"Revisa cada {cfg.get('intervalo_min', 120)} min • "
                          f"Mínimo {cfg.get('min_videos_dia', 3)}/día • "
                          f"EN con subs ES: {', '.join(cfg.get('english_nichos', []))}",
                 text_color=TEXTO, font=("Arial", 12)).pack(padx=10, pady=10)
    ctk.CTkLabel(fv, text="Eventos (fútbol/economía/noticias) siempre ASAP. "
                          "Evergreen 11-23h Colombia. Freno: cuota YouTube.",
                 text_color=SUB, font=("Arial", 11)).pack(padx=10)

    # == Historial ==
    fh = tabs.tab("Historial")
    hist_box = ctk.CTkTextbox(fh, height=110, width=660, fg_color=FONDO, font=("Consolas", 11))
    hist_box.pack(padx=10, pady=8)
    hist_box.configure(state="disabled")

    def refrescar_historial():
        e = load_estado()
        stats = e.get("stats", {})
        hist_box.configure(state="normal")
        hist_box.delete("1.0", "end")
        tot = 0
        for h in reversed(e.get("historial", [])[-30:]):
            v = stats.get(h.get("yt") or "", {}).get("views")
            if v is not None:
                tot += v
                extra = f" | {v} vistas"
            else:
                extra = ""
            marca = "YT " + h["yt"] if h.get("yt") else "sin subir"
            hist_box.insert("end", f"[{h.get('fecha')}] [{h.get('nicho')}] {h.get('titulo','')[:50]} -> {marca}{extra}\n")
        if tot:
            hist_box.insert("end", f"\nTotal muestra: {tot} vistas\n")
        top = e.get("top_nichos", [])
        if top:
            hist_box.insert("end", f"Top nichos: {', '.join(top[:3])}\n")
        hist_box.configure(state="disabled")

    # ---- log ----
    txt = ctk.CTkTextbox(root, height=180, fg_color="#0a0418", text_color=TEXTO, font=("Consolas", 11))
    txt.pack(fill="both", expand=True, padx=16, pady=8)
    txt.tag_config("err", foreground="#ff6b6b")
    txt.tag_config("ok", foreground="#3ddc84")
    txt.configure(state="disabled")

    def log(msg, tag=None):
        txt.configure(state="normal")
        if msg.startswith("ERROR"):
            txt.insert("end", msg + "\n", "err")
        elif msg.startswith("OK"):
            txt.insert("end", msg + "\n", "ok")
        else:
            txt.insert("end", msg + "\n")
        txt.see("end")
        txt.configure(state="disabled")

    def tarea(fn):
        trabajando["n"] += 1
        prog.configure(mode="indeterminate")
        prog.start()

        def run():
            try:
                fn()
            finally:
                q.put(("__fin__", None))
        threading.Thread(target=run, daemon=True).start()

    def detectar():
        def go():
            import contextlib
            with contextlib.redirect_stdout(LogCola(q)):
                ts = get_tendencias(nicho.get(), limit=5)
            if ts:
                q.put(("tema", ts[0]["titulo"]))
                q.put(("ctx", ts[0].get("hechos", "")))
                q.put((None, f"Tendencia [{nicho.get()}]: {ts[0]['titulo']}"))
            else:
                q.put((None, f"Sin tendencias para {nicho.get()} ahora."))
        tarea(go)

    def publicar(vista):
        def go():
            import contextlib
            t = {"titulo": tema_var.get().strip() or "Tema KALADOR del dia",
                 "hechos": ctx.get("1.0", "end").strip(), "nicho": nicho.get()}
            with contextlib.redirect_stdout(LogCola(q)):
                try:
                    r = run_un_video(nicho.get(), cfg, subir=not vista,
                                     trend=t, persona=persona_var.get().strip())
                    q.put(("OK", "OK: " + (r["youtube_id"] if r and r.get("youtube_id") else "vista previa lista")))
                except Exception as ex:
                    q.put(("ERROR", f"ERROR: {ex}"))
        tarea(go)

    def vigilancia(on):
        if on:
            if vig["t"] and vig["t"].is_alive():
                log("Vigilancia ya activa.")
                return
            stop.clear()
            vig["t"] = threading.Thread(target=daemon, args=(cfg, stop), daemon=True)
            vig["t"].start()
            log("Vigilancia INICIADA.", "OK")
        else:
            stop.set()
            log("Deteniendo vigilancia...")
        refrescar_stats()

    def abrir_carpeta():
        try:
            os.startfile(cfg.get("ruta_salida", "output"))
        except Exception as ex:
            log(f"ERROR: {ex}")

    def mkbtn(parent, texto, fn, oro=False):
        b = ctk.CTkButton(parent, text=texto, command=fn, corner_radius=10,
                          fg_color=ORO if oro else "#241645",
                          hover_color="#e0a800" if oro else "#37246e",
                          text_color="#000000" if oro else TEXTO,
                          font=("Arial", 12, "bold"))
        b.pack(side="left", padx=4)
        return b

    mkbtn(fb, "Detectar", detectar)
    mkbtn(fb, "Vista previa", lambda: publicar(True))
    mkbtn(fb, "PUBLICAR", lambda: publicar(False), oro=True)
    def autostart_toggle():
        try:
            from bot_autostart import activar, desactivar, activo
            import sys
            if activo():
                desactivar()
                log("Autostart OFF.")
            else:
                exe = sys.executable if getattr(sys, "frozen", False) else "python"
                if getattr(sys, "frozen", False):
                    activar(os.path.dirname(exe))
                else:
                    log("Autostart solo disponible en el .exe.")
                    return
                log("Autostart ON: vigilancia con Windows.", "OK")
        except Exception as ex:
            log(f"ERROR: {ex}")

    fvb = ctk.CTkFrame(fv, fg_color="transparent")
    fvb.pack(pady=8)
    mkbtn(fvb, "▶ Iniciar vigilancia", lambda: vigilancia(True), oro=True)
    mkbtn(fvb, "■ Detener", lambda: vigilancia(False))
    mkbtn(fvb, "Iniciar con Windows", autostart_toggle)
    fhb = ctk.CTkFrame(fh, fg_color="transparent")
    fhb.pack(pady=4)
    mkbtn(fhb, "Actualizar", lambda: (refrescar_historial(), refrescar_stats()))
    mkbtn(fhb, "Abrir carpeta", abrir_carpeta)

    def vaciar():
        while not q.empty():
            k, v = q.get()
            if k == "__fin__":
                trabajando["n"] -= 1
                if trabajando["n"] <= 0:
                    trabajando["n"] = 0
                    prog.stop()
                    prog.set(0)
                refrescar_stats()
                refrescar_historial()
            elif k == "tema":
                tema_var.set(v)
            elif k == "ctx":
                ctx.delete("1.0", "end")
                ctx.insert("1.0", v)
            elif k in ("OK", "ERROR"):
                log(v, k)
            else:
                log(v)
        root.after(400, vaciar)

    refrescar_stats()
    refrescar_historial()
    pulso()
    vaciar()
    root.mainloop()
