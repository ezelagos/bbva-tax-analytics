# Bank Tax Analytics: ETL + SQL + BI

Este proyecto implementa un **pipeline de datos fiscales** inspirado en casos reales de bancos y organismos tributarios en Argentina.  
El objetivo es integrar, limpiar y analizar información de **IVA** e **Ingresos Brutos (IIBB)**, simulando el entorno de un banco o un área impositiva corporativa.  

Se utilizan herramientas de **Python (ETL)**, **SQL (Teradata style)** y **Power BI** para análisis visual.

---

## Estructura del proyecto

bank-tax-analytics/
├── bi/ # Dashboards en Power BI
│ └── impuestos.pbix
├── config.yaml # Configuración del pipeline
├── data/
│ ├── raw/ # Datos crudos (no se suben completos al repo)
│ │ ├── loans_sample_100.csv
│ │ └── ref_.csv
│ └── processed/ # Datos procesados (excluidos del repo)
├── docs/ # Documentación adicional
│ └── controles.md
├── logs/ # Logs de ejecución (excluidos del repo)
├── sql/ # Consultas SQL de apoyo
├── src/ # Código fuente
│ ├── etl_tax.py # ETL fiscal
│ ├── util_tax.py # Funciones auxiliares
│ ├── validate.py # Validación de calidad de datos
│ ├── launcher.py # Lanzador del pipeline
│ └── run-.bat # Scripts rápidos de ejecución en Windows
├── requirements.txt # Dependencias del proyecto
└── README.md # Documentación del proyecto

markdown
Copiar código

---

## Tecnologías utilizadas

- **Python 3.10**
  - `pandas`, `numpy` → procesamiento de datos  
  - `pyyaml` → configuración del pipeline  
  - `sqlalchemy` → consultas SQL (simulación de entorno Teradata)  
  - `pyarrow` / `fastparquet` → almacenamiento en parquet  
- **SQL** → reglas de negocio, queries estilo Teradata  
- **Power BI** → visualización de métricas y KPIs  

---

## Flujo ETL

### 1. Extracción
- Lectura de CSVs crudos (`loans.csv`, `ref_alicuotas_iibb.csv`, `ref_iva_servicios.csv`).  
- Carga de parámetros desde `config.yaml`.

### 2. Transformación
- Cálculo de impuestos:
  - **IVA** → débito/crédito según facturación.  
  - **IIBB** → aplicación de alícuotas según actividad.  
- Limpieza y normalización de CUITs.  
- Enriquecimiento con tablas de referencia.

### 3. Validación
- Script `validate.py` con **data quality checks**:
  - Nulos
  - Valores fuera de rango
  - Alícuotas inválidas

### 4. Carga
- Generación de CSVs procesados (`DDJJ_IIBB_detalle.csv`, `DDJJ_IVA_detalle.csv`, `DDJJ_consolidado.csv`).  
- Listos para análisis o dashboards.

---

## BI y Resultados

En **Power BI** (`bi/impuestos.pbix`) se analizan:

- Evolución temporal de IVA e IIBB.  
- Comparativa por jurisdicción y actividad.  
- KPI de cumplimiento y desvíos.  

---

## Ejecución rápida

### 1. Clonar el repo
```bash
git clone https://github.com/ezelagos/bank-tax-analytics.git
cd bank-tax-analytics
### 2. Crear y activar entorno
bash
Copiar código
python3 -m venv .venv
source .venv/bin/activate
### 3. Instalar dependencias
bash
Copiar código
pip install -r requirements.txt
### 4. Ejecutar ETL completo
bash
Copiar código
python src/etl_tax.py
### 5. Validar calidad de datos
bash
Copiar código
python src/validate.py