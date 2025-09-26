# src/launcher.py
import os
import sys
import importlib
import logging
from datetime import datetime
from typing import Optional

# . Layout por defecto (ajustá si tu repo difiere) ........==
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RAW = os.path.normpath(os.path.join(REPO_ROOT, "..", "data", "raw"))
DEFAULT_OUT = os.path.normpath(os.path.join(REPO_ROOT, "..", "data", "processed"))
DEFAULT_LOG = os.path.normpath(os.path.join(REPO_ROOT, "..", "logs"))

# . Logging del launcher .....=
os.makedirs(DEFAULT_LOG, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DEFAULT_LOG, "launcher.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# . Utils de entrada ......==
def _pick_file(prompt: str, folder: str, pattern: Optional[str] = None) -> str:
    """Lista archivos de 'folder' y permite elegir uno. Devuelve ruta absoluta."""
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if pattern:
        files = [f for f in files if pattern.lower() in f.lower()]
    if not files:
        raise FileNotFoundError(
            f"No se encontraron archivos en {folder}"
            + (f" (filtro: {pattern})" if pattern else "")
        )

    print(f"\n{prompt} (carpeta: {folder})")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f}")
    while True:
        try:
            idx = int(input("Elegí número: ").strip())
            if 1 <= idx <= len(files):
                return os.path.join(folder, files[idx - 1])
        except Exception:
            pass
        print("Opción inválida, probá de nuevo.")

def _confirm(msg: str, default_no: bool = True) -> bool:
    ans = input(f"{msg} [{'s/N' if default_no else 'S/n'}]: ").strip().lower()
    if ans == "" and default_no:
        return False
    if ans == "" and not default_no:
        return True
    return ans in ("s", "si", "y", "yes")

def _input_path(label: str, default_path: str) -> str:
    path = input(f"{label} [{default_path}]: ").strip()
    return path or default_path

# . Config de rutas .......
def configure_paths() -> tuple[str, str, str]:
    print("\n. Configurar rutas .")
    raw = _input_path("RAW", DEFAULT_RAW)
    out = _input_path("OUT", DEFAULT_OUT)
    log = _input_path("LOGDIR", DEFAULT_LOG)
    for p in (raw, out, log):
        os.makedirs(p, exist_ok=True)
    logging.info(f"Usando RAW={raw} | OUT={out} | LOGDIR={log}")
    return raw, out, log

# . Alias/Enlace de archivos sin copiar 
def _ensure_alias(src_path: str, dst_folder: str, dst_name: str):

    src_path = os.path.abspath(src_path)
    dst_path = os.path.abspath(os.path.join(dst_folder, dst_name))

    if src_path == dst_path:
        logging.info(f"Alias innecesario (mismo archivo): {dst_path}")
        return

    # Quitar destino previo
    try:
        if os.path.exists(dst_path) or os.path.islink(dst_path):
            os.remove(dst_path)
    except Exception as e:
        logging.warning(f"No pude remover destino previo {dst_path}: {e}")

    # 1) Hardlink
    try:
        os.link(src_path, dst_path)
        logging.info(f"Hardlink creado: {dst_path} → {src_path}")
        return
    except Exception as e:
        logging.info(f"Hardlink no disponible, probando symlink. Motivo: {e}")

    # 2) Symlink
    try:
        os.symlink(src_path, dst_path)
        logging.info(f"Symlink creado: {dst_path} → {src_path}")
        return
    except Exception as e:
        logging.info(f"Symlink no disponible, se copiará. Motivo: {e}")

    # 3) Copia (último recurso)
    try:
        import shutil
        shutil.copy2(src_path, dst_path)
        logging.info(f"Copiado temporal: {dst_path} (desde {src_path})")
    except Exception as e:
        logging.error(f"No pude crear alias/copia para {dst_name}: {e}")
        raise

# . Carga dinámica del módulo ETL ..
def _load_etl_module():
    try:
        sys.path.insert(0, REPO_ROOT)  # asegurar import desde src/
        etl_tax = importlib.import_module("etl_tax")
        importlib.reload(etl_tax)
        return etl_tax
    except Exception as e:
        logging.error(f"No pude importar etl_tax: {e}", exc_info=True)
        raise

# . Corridas .........
def run_etl_interactive():
    """Corre etl_tax con selección interactiva de rutas/archivos y opciones de rendimiento."""
    raw, out, logdir = configure_paths()

    print("\nElegí los archivos a utilizar (Enter para usar nombres por defecto).")
    try:
        loans_csv = (
            _pick_file("Seleccioná loans.csv", raw, pattern="loan")
            if _confirm("¿Elegir loans.csv manualmente?")
            else os.path.join(raw, "loans.csv")
        )
        iibb_csv = (
            _pick_file("Seleccioná ref_alicuotas_iibb.csv", raw, pattern="iibb")
            if _confirm("¿Elegir ref_alicuotas_iibb.csv manualmente?")
            else os.path.join(raw, "ref_alicuotas_iibb.csv")
        )
        iva_csv = (
            _pick_file("Seleccioná ref_iva_servicios.csv", raw, pattern="iva")
            if _confirm("¿Elegir ref_iva_servicios.csv manualmente?")
            else os.path.join(raw, "ref_iva_servicios.csv")
        )
    except FileNotFoundError as e:
        logging.error(str(e))
        return

    # Chequeos mínimos
    for f in (loans_csv, iibb_csv, iva_csv):
        if not os.path.exists(f):
            logging.error(f"Falta archivo requerido: {f}")
            return

    etl_tax = _load_etl_module()

    # Monkeypatch de paths
    etl_tax.RAW = raw
    etl_tax.OUT = out
    etl_tax.LOGDIR = logdir

    # Modo rápido (desactiva profilings y otros costos si tu etl lo soporta)
    if _confirm("¿Activar FAST_MODE en etl_tax (recomendado para datasets grandes)?", default_no=False):
        try:
            setattr(etl_tax, "FAST_MODE", True)
            logging.info("FAST_MODE = True aplicado en etl_tax")
        except Exception:
            logging.info("etl_tax no define FAST_MODE; se ignora.")

    # Crear alias/links a nombres esperados
    if _confirm("¿Forzar que etl use exactamente los archivos elegidos (crear hardlink/symlink/copia si hace falta)?"):
        _ensure_alias(loans_csv, raw, "loans.csv")
        _ensure_alias(iibb_csv, raw, "ref_alicuotas_iibb.csv")
        _ensure_alias(iva_csv,  raw, "ref_iva_servicios.csv")
    else:
        logging.info("No se forzaron alias; se usarán los nombres por defecto en RAW.")

    # Ejecutar
    t0 = datetime.now()
    logging.info("Lanzando etl_tax.main()")
    try:
        etl_tax.main()
        logging.info("etl_tax finalizó OK")
    except Exception as e:
        logging.error(f"Falla ejecutando etl_tax.main(): {e}", exc_info=True)
    finally:
        logging.info(f"Duración total: {datetime.now() - t0}")

def quick_run(raw: str = DEFAULT_RAW, out: str = DEFAULT_OUT, logdir: str = DEFAULT_LOG, fast_mode: bool = True):
    for p in (raw, out, logdir):
        os.makedirs(p, exist_ok=True)

    etl_tax = _load_etl_module()
    etl_tax.RAW, etl_tax.OUT, etl_tax.LOGDIR = raw, out, logdir
    if fast_mode:
        try:
            setattr(etl_tax, "FAST_MODE", True)
        except Exception:
            pass

    t0 = datetime.now()
    logging.info(f"Quick run (FAST_MODE={getattr(etl_tax, 'FAST_MODE', False)})")
    ok = True
    try:
        etl_tax.main()
    except Exception as e:
        ok = False
        logging.error(f"quick_run falló: {e}", exc_info=True)
    finally:
        logging.info(f"Duración total: {datetime.now() - t0}")
        if ok:
            logging.info("etl_tax finalizó OK")
        else:
            logging.info("etl_tax finalizó con ERRORES")


# . Utilidad: crear sample rápido ..
def create_sample_and_run(nrows: int = 100):
    raw, out, logdir = DEFAULT_RAW, DEFAULT_OUT, DEFAULT_LOG
    for p in (raw, out, logdir):
        os.makedirs(p, exist_ok=True)

    full_path = os.path.join(raw, "loans.csv")
    sample_path = os.path.join(raw, f"loans_sample_{nrows}.csv")
    if not os.path.exists(full_path):
        print(f"No se encontró {full_path}, imposible crear sample.")
        return

    import pandas as pd
    logging.info(f"Creando sample de {nrows} filas desde {full_path}")
    df = pd.read_csv(full_path, nrows=nrows, low_memory=False)
    df.to_csv(sample_path, index=False)
    logging.info(f"Sample creado en {sample_path} con {len(df)} filas.")

    # Forzar alias para usar el sample como loans.csv sin copiar
    _ensure_alias(sample_path, raw, "loans.csv")

    # Ejecutar rápido
    quick_run(raw=raw, out=out, logdir=logdir, fast_mode=True)

# . Menú principal .......
def main_menu():
    while True:
        print(
            """
.....== LAUNCHER BBVA TAX .....==
[1] Ejecutar ETL (interactivo: elegir paths y CSV)
[2] Ejecutar ETL rápido (por defecto)
[3] Mostrar rutas por defecto
[4] Crear sample de loans (100 filas) y correr ETL
[0] Salir
"""
        )
        choice = input("Opción: ").strip()
        if choice == "1":
            run_etl_interactive()
        elif choice == "2":
            quick_run()
        elif choice == "3":
            print(f"RAW={DEFAULT_RAW}\nOUT={DEFAULT_OUT}\nLOGDIR={DEFAULT_LOG}")
        elif choice == "4":
            create_sample_and_run(100)
        elif choice == "0":
            break
        else:
            print("Opción inválida.")

# . Entrypoint ........=
if __name__ == "__main__":
    # Atajos por CLI:
    #   python src/launcher.py --fast
    #   python src/launcher.py --sample 100
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--fast":
            quick_run()
        elif arg == "--sample":
            n = 100
            if len(sys.argv) > 2:
                try:
                    n = int(sys.argv[2])
                except Exception:
                    pass
            create_sample_and_run(n)
        else:
            main_menu()
    else:
        main_menu()
