# src/validate.py
# Script de validación de esquemas según config.yaml

import os
import sys
import yaml
import logging
import pandas as pd

# ------------------------
# Setup logger
# ------------------------
log_path = os.path.join("logs", "validate.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ------------------------
# Utils
# ------------------------
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, expected_cols: list, name: str):
    missing = [col for col in expected_cols if col not in df.columns]
    extra = [col for col in df.columns if col not in expected_cols]

    if missing:
        logger.error(f" {name}: faltan columnas {missing}")
    else:
        logger.info(f" {name}: todas las columnas requeridas están presentes")

    if extra:
        logger.warning(f" {name}: columnas extra encontradas {extra}")

# ------------------------
# Main
# ------------------------
def main():
    cfg = load_config()

    # Recorremos los esquemas definidos en config
    for dataset, rules in cfg.get("schemas", {}).items():
        required = rules.get("required_columns", [])
        input_path = None

        # Buscar dataset en raw o processed
        for folder in ["data/raw", "data/processed"]:
            candidate = os.path.join(folder, f"{dataset}.csv")
            if os.path.exists(candidate):
                input_path = candidate
                break

        if not input_path:
            logger.error(f" No se encontró el archivo para {dataset}")
            continue

        try:
            df = pd.read_csv(input_path)
            logger.info(f"Validando {dataset} ({len(df):,} filas)")
            validate_schema(df, required, dataset)
        except Exception as e:
            logger.error(f"❌ Error al leer {dataset}: {e}")

if __name__ == "__main__":
    main()
