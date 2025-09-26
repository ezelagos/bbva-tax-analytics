import os, logging
import pandas as pd
from util_tax import (
    load, clean_df, clean_dates, normalize_types, prep,
    calc_iibb, calc_iva, profile_df
)

# Config
OUT = r"C:\Users\Eze\Desktop\bbva-tax-analytics\data\processed"
LOGDIR = r"C:\Users\Eze\Desktop\bbva-tax-analytics\logs"
FAST_MODE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{LOGDIR}/etl_tax.log", encoding="utf-8")
    ]
)

def export(iibb: pd.DataFrame, iva: pd.DataFrame):
    logging.info("Exportando archivos DDJJ...")

    os.makedirs(OUT, exist_ok=True)

    ddjj_iibb = (
        iibb.groupby("periodo", as_index=False)["iibb"].sum()
        .assign(regimen="IIBB")
        .rename(columns={"iibb": "importe"})
    )

    ddjj_iva = (
        iva.groupby("periodo", as_index=False)["debito_iva"].sum()
        .assign(regimen="IVA")
        .rename(columns={"debito_iva": "importe"})
    )

    ddjj = pd.concat([ddjj_iibb, ddjj_iva], ignore_index=True)

    iibb.to_csv(f"{OUT}/DDJJ_IIBB_detalle.csv", index=False)
    iva.to_csv(f"{OUT}/DDJJ_IVA_detalle.csv", index=False)
    ddjj.to_csv(f"{OUT}/DDJJ_consolidado.csv", index=False)

    logging.info(f"Archivos generados en {OUT}/")
    logging.info(f"   - DDJJ_IIBB_detalle.csv ({len(iibb)} filas)")
    logging.info(f"   - DDJJ_IVA_detalle.csv ({len(iva)} filas)")
    logging.info(f"   - DDJJ_consolidado.csv ({len(ddjj)} filas)")

def main():
    logging.info("Inicio del proceso ETL fiscal")
    try:
        loans, ref_iibb, ref_iva = load()

        if not FAST_MODE:
            profile_df(loans, "loans")

        loans = clean_df(loans)
        loans = clean_dates(loans)
        loans = normalize_types(loans)

        if not FAST_MODE:
            profile_df(loans, "loans_clean")

        loans = prep(loans)
        iibb = calc_iibb(loans, ref_iibb)
        iva = calc_iva(loans, ref_iva)

        export(iibb, iva)

        logging.info("ETL fiscal finalizado con éxito")
    except Exception as e:
        logging.error(f"Error en el ETL Fiscal: {e}", exc_info=True)

if __name__ == "__main__":
    main()
