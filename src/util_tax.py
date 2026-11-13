import pandas as pd
import logging
import os
from datetime import datetime

# =========================
# Configuración
# =========================
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

RAW = str(ROOT / "data" / "raw")
LOGDIR = "logs"
os.makedirs(LOGDIR, exist_ok=True)

# =========================
# Funciones de CUIT
# =========================
def log_cuit(member_id, cuit, metodo):
    """Registra generación de CUIT en logs/cuit_generados.csv"""
    ctrl_path = f"{LOGDIR}/cuit_generados.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "fecha": now,
        "member_id": member_id,
        "cuit_cliente": cuit,
        "metodo": metodo
    }
    df_record = pd.DataFrame([record])
    if os.path.exists(ctrl_path):
        df_record.to_csv(ctrl_path, mode="a", header=False, index=False)
    else:
        df_record.to_csv(ctrl_path, mode="w", header=True, index=False)


def cuit_from_member(member_id) -> str:
    try:
        if pd.isna(member_id):
            cuit = "20999999999"
            logging.warning("member_id vacío imputado con CUIT fallback")
            log_cuit(member_id, cuit, "fallback_nan")
            return cuit

        member_id = str(member_id).strip()
        base = f"20{int(float(member_id)):08d}"[:10]
        coef = [5,4,3,2,7,6,5,4,3,2]
        s = sum(int(d)*c for d,c in zip(base, coef))
        dv = 11 - (s % 11)
        dv = 0 if dv == 11 else (9 if dv == 10 else dv)
        cuit = base + str(dv)

        log_cuit(member_id, cuit, "normal")
        return cuit

    except Exception as e:
        cuit = "20999999999"
        logging.error(f"CUIT fallback usado para member_id={member_id} | Error: {e}")
        log_cuit(member_id, cuit, "fallback_error")
        return cuit

# =========================
# Funciones ETL
# =========================
def load():
    """Carga datasets RAW desde carpeta /data/raw"""
    loans = pd.read_csv(f"{RAW}/loans.csv")
    ref_iibb = pd.read_csv(f"{RAW}/ref_alicuotas_iibb.csv")
    ref_iva = pd.read_csv(f"{RAW}/ref_iva_servicios.csv")
    logging.info(f"Datasets cargados: loans={len(loans)}, iibb_ref={len(ref_iibb)}, iva_ref={len(ref_iva)}")
    return loans, ref_iibb, ref_iva


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte issue_d en datetime y crea periodo AAAAMM"""
    if "issue_d" in df.columns:
        df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y", errors="coerce")
        df["periodo"] = df["issue_d"].dt.year.astype(str) + df["issue_d"].dt.month.astype(str).str.zfill(2)

    logging.info(f"Periodos únicos tras clean_dates: {df['periodo'].dropna().unique()[:10]}")
    return df


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


def prep(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


def calc_iibb(loans: pd.DataFrame, ref_iibb: pd.DataFrame) -> pd.DataFrame:
    df = loans.copy()
    df["jurisdiccion"] = df["addr_state"]
    df["base_iibb"] = df["loan_amnt"]

    df = df.merge(ref_iibb, how="left", on="jurisdiccion")
    df["alicuota"] = df["alicuota"].fillna(0)
    df["iibb"] = df["base_iibb"] * (df["alicuota"] / 100)

    logging.info(f"Periodos únicos en IIBB: {df['periodo'].dropna().unique()[:10]}")
    return df[["periodo", "jurisdiccion", "base_iibb", "alicuota", "iibb"]]


def calc_iva(loans: pd.DataFrame, ref_iva: pd.DataFrame) -> pd.DataFrame:
    df = loans.copy()
    df["base_gravada"] = df["loan_amnt"]

    df = df.merge(ref_iva, how="left", on="purpose")
    df["tasa_iva"] = df["tasa_iva"].fillna(0)
    df["debito_iva"] = df["base_gravada"] * df["tasa_iva"]

    logging.info(f"Periodos únicos en IVA: {df['periodo'].dropna().unique()[:10]}")
    return df[["periodo", "purpose", "base_gravada", "tasa_iva", "debito_iva"]]


def profile_df(df: pd.DataFrame, name: str):
    logging.info(f"Perfilando {name}: filas={df.shape[0]}, columnas={df.shape[1]}")
