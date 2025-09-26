# BBVA Tax Analytics (Demo)
Pipeline ETL en Python para calcular IVA e IIBB a partir de préstamos. Incluye:
- Imputación controlada y trazable (logs/imputaciones.csv)
- CUIT sintético y fallback seguro
- Mapeo jurisdicción US→AR
- KPIs en Power BI: IVA, IIBB y Calidad de Datos

## Cómo correr
- Doble click: run-fast.bat  (dataset completo en FAST_MODE)
- Doble click: run-sample.bat (sample de 100 filas)
- Manual: python src/launcher.py --fast

## Entradas
- data/raw/loans.csv
- data/raw/ref_alicuotas_iibb.csv
- data/raw/ref_iva_servicios.csv

## Salidas
- data/processed/DDJJ_IIBB_detalle.csv
- data/processed/DDJJ_IVA_detalle.csv
- data/processed/DDJJ_consolidado.csv
- logs/*.csv y etl_tax.log
