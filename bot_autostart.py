"""Autostart sin dependencias: .bat en shell:startup (vigilancia con Windows)."""
import os

NOMBRE = "KALADOR_daemon.bat"


def ruta_startup():
    base = os.path.join(os.environ.get("APPDATA", ""),
                        r"Microsoft\Windows\Start Menu\Programs\Startup")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, NOMBRE)


def activar(exe_dir):
    dest = ruta_startup()
    with open(dest, "w") as f:
        f.write(f'@echo off\ncd /d "{exe_dir}"\nstart "KALADOR" /min KALADOR.exe --daemon\n')
    print("Autostart ON:", dest)
    return dest


def desactivar():
    dest = ruta_startup()
    if os.path.exists(dest):
        os.remove(dest)
        print("Autostart OFF")
        return True
    print("Autostart no estaba activo")
    return False


def activo():
    return os.path.exists(ruta_startup())
