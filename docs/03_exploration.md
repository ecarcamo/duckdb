# Ejercicio 3 — Consultas directas sobre archivos Parquet

Notebook ejecutado: [notebooks/03_exploration.ipynb](../notebooks/03_exploration.ipynb).
Consultas: [sql/03_exploration/](../sql/03_exploration/).

Datos explorados: 16 archivos de 2026 (enero a agosto, taxis amarillos y verdes)
descargados en el Ejercicio 2. Ninguna consulta importa los datos a una tabla:
DuckDB lee los archivos Parquet cada vez que se ejecuta la consulta.

## Cómo se ejecutan las consultas

`scripts/taxi_db.py` abre una conexión de DuckDB en memoria con la raíz del
proyecto como directorio de trabajo, de modo que las rutas `data/raw/...` de los
archivos SQL funcionan desde cualquier lugar. También crea cuatro vistas, que
son consultas guardadas (no copias de los datos):

| Vista | Archivo | Qué hace |
|---|---|---|
| `yellow_raw`, `green_raw` | `sql/views/raw.sql` | `read_parquet` sobre todos los archivos de cada tipo con `union_by_name = true` y `filename = true`. |
| `trips` | `sql/views/trips.sql` | Une ambos tipos con `UNION ALL BY NAME`, renombra `tpep_*`/`lpep_*` a `pickup_datetime` y `dropoff_datetime`, y agrega `taxi_type`, `source_year` y `source_month` (obtenidos del nombre del archivo). |
| `trips_clean` | `sql/views/trips_clean.sql` | Aplica las reglas de calidad decididas en este ejercicio y agrega `duration_minutes`. |
| `zones` | `sql/views/zones.sql` | Lee `taxi_zone_lookup.csv` (código de zona → distrito y nombre). |

## Documentación de cada consulta

Los archivos fuente son siempre los Parquet de `data/raw/`; se indica el patrón usado.

### 01 — Inventario de archivos (`01_file_inventory.sql`)

- **Objetivo:** contar los archivos disponibles por tipo y año (3.1).
- **Fuente:** `glob('data/raw/*/*/*.parquet')` (solo nombres, no abre los archivos).
- **Resultado:** 16 archivos: 8 amarillos y 8 verdes, de `2026-01` a `2026-08`.
- **Decisión:** el inventario coincide con lo publicado por la TLC; la ruta
  `data/raw/<tipo>/<año>/` permite obtener tipo y año sin leer los datos.

### 02 — Registros por archivo según metadatos (`02_rows_per_file.sql`)

- **Objetivo:** obtener el número de filas de cada archivo sin leer los datos (3.2).
- **Fuente:** `parquet_metadata` y `parquet_file_metadata` sobre `data/raw/*/*/*.parquet`.
- **Resultado:** cada archivo amarillo tiene entre 3,336,716 y 4,090,836 filas
  en 4 grupos de filas (row groups) y ocupa entre 56 y 67 MiB comprimido
  (≈ 86–104 MiB sin comprimir). Cada archivo verde tiene entre 37,373 y 44,921
  filas en un solo grupo (≈ 1 MiB).
- **Decisión:** los conteos coinciden con los de `--verify` del Ejercicio 2. Los
  metadatos permiten contar filas en milisegundos (la consulta tardó 0.01 s).

### 03 — Conteo de registros leyendo los datos (`03_total_rows.sql`)

- **Objetivo:** confirmar el número de registros leyendo las filas (3.2).
- **Fuente:** `read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)`.
- **Resultado:**

  | Tipo | Viajes |
  |---|---|
  | yellow | 29,703,355 |
  | green | 337,114 |
  | total | 30,040,469 |

- **Decisión:** los taxis verdes representan solo el 1.1 % de los viajes, por lo
  que cualquier comparación entre tipos debe usar promedios o porcentajes, no
  totales.

### 04 — Columnas por tipo de archivo (`04_columns_by_file.sql`)

- **Objetivo:** identificar las columnas presentes en cada archivo (3.3).
- **Fuente:** `parquet_schema('data/raw/*/*/*.parquet')`.
- **Resultado:** 17 columnas son comunes a ambos tipos. Los amarillos tienen
  `tpep_pickup_datetime`, `tpep_dropoff_datetime` y `Airport_fee`; los verdes
  tienen `lpep_pickup_datetime`, `lpep_dropoff_datetime`, `ehail_fee` y
  `trip_type`. La columna `request_source` aparece **solo desde junio de 2026**
  (3 archivos de cada tipo).
- **Decisión:** los esquemas no son idénticos ni entre tipos ni entre meses. Se
  usa `union_by_name = true` para que DuckDB alinee las columnas por nombre y
  rellene con `NULL` las que faltan, y la vista `trips` renombra las fechas para
  poder consultar ambos tipos con el mismo SQL.

### 05 y 06 — Tipos de datos (`05_column_types_yellow.sql`, `06_column_types_green.sql`)

- **Objetivo:** determinar el tipo lógico de cada columna (3.4).
- **Fuente:** `DESCRIBE` sobre `read_parquet('data/raw/<tipo>/*/*.parquet', union_by_name = true)`.
- **Resultado:** fechas `TIMESTAMP`; `VendorID`, `PULocationID` y
  `DOLocationID` `INTEGER`; `passenger_count`, `RatecodeID`, `payment_type` y
  `trip_type` `BIGINT`; montos y distancia `DOUBLE`; `store_and_fwd_flag` y
  `request_source` `VARCHAR`.
- **Decisión:** los códigos (`payment_type`, `RatecodeID`, `VendorID`) son
  enteros categóricos, no medidas: en el análisis se agrupan, no se promedian.

### 07 — Conflictos de tipos (`07_type_conflicts.sql`)

- **Objetivo:** detectar columnas cuyo tipo cambia entre archivos (3.4).
- **Fuente:** `parquet_schema('data/raw/*/*/*.parquet')`.
- **Resultado:** ninguna columna cambia de tipo físico en 2026.
- **Decisión:** la consulta se conserva para volver a ejecutarla al agregar
  otros años (Ejercicios 5 y 8).

### 08 y 09 — Muestras (`08_sample_yellow.sql`, `09_sample_green.sql`)

- **Objetivo:** observar registros reales (3.5).
- **Fuente:** `read_parquet` con `USING SAMPLE reservoir(5 ROWS) REPEATABLE (42)`.
- **Resultado:** las filas son coherentes en general, pero la suma de los
  componentes no siempre coincide con `total_amount`. En los viajes del
  proveedor 2 sí coincide (7.20 + extra 1.00 + MTA 0.50 + propina 2.44 +
  mejora 1.00 + congestión 2.50 = 14.64). En los del proveedor 1 el campo
  `extra` ya incluye los recargos de congestión: 7.90 + extra 3.50 + MTA 0.50 +
  propina 3.20 + mejora 1.00 = 16.10, aunque `congestion_surcharge` también
  reporta 2.50. Aparece `cbd_congestion_fee = 0.75` (cargo por entrar a la zona
  de congestión de Manhattan).
- **Decisión:** `total_amount` se usa como la medida de ingreso del viaje y no
  se recalcula sumando componentes; la propina se analiza como porcentaje de
  `fare_amount`.

### 10 y 11 — Perfil estadístico (`10_summary_yellow.sql`, `11_summary_green.sql`)

- **Objetivo:** encontrar valores imposibles, extremos y nulos (3.6).
- **Fuente:** `SUMMARIZE` sobre `read_parquet` de cada tipo.
- **Resultado (amarillos):**
  - `tpep_pickup_datetime` mínimo `2001-01-01`, aunque los archivos son de 2026.
  - `trip_distance` máximo 328,522 millas; mediana 1.86 millas.
  - `fare_amount` entre −2,555.20 y 7,045.00; `total_amount` entre −2,560.20 y 7,053.50.
  - `passenger_count`, `RatecodeID`, `store_and_fwd_flag`,
    `congestion_surcharge` y `Airport_fee` tienen **25.98 %** de nulos.
  - `RatecodeID` llega a 99 (código no documentado) y `VendorID` incluye 6 y 7.
- **Resultado (verdes):** `ehail_fee` 100 % nulo; 14.47 % de nulos en
  `passenger_count`, `payment_type`, `trip_type` y otras; distancia máxima de
  179,830.92 millas; fecha mínima `2008-12-31`.
- **Decisión:** se necesitan reglas explícitas de calidad (consulta 12);
  `ehail_fee` no se usa en el análisis.

### 12 — Reglas de calidad (`12_quality_checks.sql`)

- **Objetivo:** cuantificar cada problema de calidad (3.6).
- **Fuente:** vista `trips` (lee `data/raw/*/*/*.parquet`).
- **Resultado:**

  | Problema | Yellow | % | Green | % |
  |---|---|---|---|---|
  | `passenger_count` nulo | 7,716,688 | 25.98 | 48,775 | 14.47 |
  | `payment_type = 0` | 7,716,688 | 25.98 | 0 | 0.00 |
  | Distancia 0 | 952,231 | 3.21 | 12,212 | 3.62 |
  | `RatecodeID = 99` | 769,693 | 2.59 | 2 | 0.00 |
  | Duración ≤ 0 | 371,683 | 1.25 | 234 | 0.07 |
  | Zona desconocida (264/265) | 201,486 | 0.68 | 5,886 | 1.75 |
  | Montos negativos | 161,970 | 0.55 | 1,025 | 0.30 |
  | 0 pasajeros | 91,359 | 0.31 | 4,527 | 1.34 |
  | Duración > 6 h | 7,315 | 0.02 | 1,104 | 0.33 |
  | Distancia > 100 millas | 1,223 | 0.00 | 72 | 0.02 |
  | Abordaje fuera del mes del archivo | 146 | 0.00 | 98 | 0.03 |
  | Total > 1000 | 49 | 0.00 | 1 | 0.00 |

- **Decisión:** ver la vista `trips_clean` más abajo.

### 13 — Rango de fechas (`13_pickup_date_range.sql`)

- **Objetivo:** confirmar que las fechas corresponden al periodo de los archivos.
- **Fuente:** vista `trips`.
- **Resultado:** 17 viajes amarillos y 14 verdes con fecha anterior a 2026
  (desde 2001 y 2008); ninguno posterior a agosto de 2026.
- **Decisión:** el periodo de un viaje se toma de la fecha de abordaje, pero solo
  se aceptan viajes cuyo abordaje cae dentro del mes del archivo que los contiene.

### 14 — Patrón de valores faltantes (`14_missing_values_pattern.sql`)

- **Objetivo:** entender por qué una cuarta parte de los amarillos no tiene
  `passenger_count`.
- **Fuente:** vista `trips`.
- **Resultado:** en los amarillos, **todos** los viajes con `passenger_count`
  nulo tienen `payment_type = 0` y viceversa (7,716,688 viajes; también tienen
  nulos `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` y
  `Airport_fee`). En los verdes, los nulos coinciden con `payment_type` nulo
  (48,775 viajes).
- **Decisión:** no es ruido aleatorio sino un tipo de registro distinto: viajes
  reportados sin los datos del taxímetro, que el diccionario de la TLC asocia
  con viajes de tarifa flexible (`payment_type = 0`). Se conservan, porque su
  fecha, distancia, zonas y montos son válidos, pero se reportan como categoría
  propia («desconocido») en el análisis de pago.

### 15 — Duplicados (`15_duplicates.sql`)

- **Objetivo:** detectar registros idénticos.
- **Fuente:** vista `trips`; se agrupa por `hash(t)` de la fila completa.
- **Resultado:** 7 filas amarillas repetidas; ningún duplicado verde.
- **Decisión:** el efecto es despreciable (7 de 29.7 millones) y no se eliminan.
  La primera versión, que agrupaba por todas las columnas, agotó el límite de
  memoria de 4 GB; agrupar por un hash de 64 bits resolvió el problema en 1.2 s.

### 18 — Duración por proveedor (`18_vendor_timestamps.sql`)

- **Objetivo:** averiguar si los viajes con duración cero o negativa son errores
  aislados o un patrón de algún proveedor.
- **Fuente:** vista `trips`.
- **Resultado:** el proveedor 7 registra la **misma hora** de abordaje y de
  descenso en sus 367,120 viajes amarillos (100 %); en los demás proveedores el
  problema afecta a menos del 0.3 % de los viajes.
- **Decisión:** la primera versión de `trips_clean` exigía
  `dropoff_datetime > pickup_datetime` y eliminaba por completo a este
  proveedor, aunque su distancia, zonas y montos son válidos. Se corrigió la
  vista: los viajes del proveedor 7 con ambas horas iguales se conservan con
  `duration_minutes` nulo, de modo que cuentan para volumen e ingresos pero no
  para las métricas de duración y velocidad. Este error se detectó en el
  Ejercicio 4 al comparar proveedores.

### 16 — Columna `request_source` (`16_request_source.sql`)

- **Objetivo:** entender la columna nueva que aparece desde junio de 2026.
- **Fuente:** vista `trips`.
- **Resultado:** en agosto, 28 % de los viajes amarillos tiene un valor:
  `HV0003` (628,774), `HV0005` (181,233), `A` (103,753), `EH0004`, `CC` y
  `EH0010`. `HV0003` y `HV0005` son las licencias de base de Uber y Lyft en la
  TLC, por lo que la columna indica que el viaje en taxi fue solicitado por medio
  de esas plataformas.
- **Decisión:** la vista `trips` no enumera columnas, así que `request_source`
  aparece sola y vale `NULL` para los meses anteriores. Se interpreta solo a
  partir de junio de 2026.

### 17 — Efecto de la limpieza (`17_clean_vs_raw.sql`)

- **Objetivo:** medir cuántos viajes descarta `trips_clean`.
- **Fuente:** vistas `trips` y `trips_clean`.
- **Resultado:**

  | Tipo | Crudos | Limpios | Descartados | % |
  |---|---|---|---|---|
  | yellow | 29,703,355 | 28,593,831 | 1,109,524 | 3.74 |
  | green | 337,114 | 322,606 | 14,508 | 4.30 |

- **Decisión:** el análisis de comportamiento (duración, distancia, tarifas)
  usa `trips_clean`; los conteos de volumen pueden usar `trips`.

## Reglas de la vista `trips_clean`

Un viaje se conserva si cumple todas estas condiciones:

| Regla | Motivo |
|---|---|
| El abordaje cae dentro del mes del archivo | Fechas de 2001 o 2008 son errores de reloj del taxímetro. |
| `dropoff_datetime > pickup_datetime`, excepto el proveedor 7 con ambas horas iguales | Una duración cero o negativa es imposible; el proveedor 7 no reporta la hora de descenso (consulta 18), así que sus viajes se conservan con duración nula. |
| Duración ≤ 6 horas | Turnos olvidados abiertos; un viaje urbano no dura medio día. |
| `0 < trip_distance ≤ 100` | Distancia cero suele ser viaje cancelado; más de 100 millas excede el área de servicio. |
| `fare_amount ≥ 0` y `0 < total_amount ≤ 1000` | Los montos negativos son reversos o ajustes contables, no viajes. |

No se filtran `passenger_count` nulo ni `payment_type = 0` (consulta 14) y no
se filtran las zonas 264/265, que se reportan como «desconocidas» cuando se
analiza la geografía.

## 3.9 ¿Qué significa consultar directamente un archivo Parquet?

Significa que DuckDB ejecuta SQL usando los archivos `.parquet` como si fueran
tablas, sin un paso previo de carga (`INSERT` o `CREATE TABLE ... AS`). La
consulta `SELECT count(*) FROM read_parquet('data/raw/*/*/*.parquet')` abre los
archivos en ese momento, lee lo necesario y devuelve el resultado; no queda
ninguna copia de los datos en una base.

Es útil con volúmenes grandes porque Parquet y DuckDB evitan leer lo que no se
necesita:

- **Formato columnar.** Cada columna se guarda por separado; una consulta que
  usa `fare_amount` y `payment_type` lee solo esas dos columnas de las 21.
- **Metadatos en el pie del archivo.** El número de filas, el esquema y el
  mínimo y máximo de cada columna por grupo de filas están en el pie. Por eso la
  consulta 02 cuenta 30 millones de filas en 0.01 s sin leer los datos, y un
  filtro por fecha puede saltarse grupos de filas completos (*predicate
  pushdown*).
- **Compresión.** Los 488 MiB de taxis amarillos de 2026 equivalen a unos
  750 MiB sin comprimir y a varios GB como CSV o como DataFrame de pandas.
- **Globs y `union_by_name`.** Un patrón como `data/raw/*/*/*.parquet` trata
  decenas de archivos mensuales como una sola tabla aunque sus esquemas difieran
  un poco; agregar un mes nuevo es copiar un archivo, no recargar una base.
- **Ejecución paralela y fuera de memoria.** DuckDB procesa los grupos de filas
  en paralelo y puede usar disco temporal (`temp_directory`) cuando una
  agregación no cabe en el límite de memoria configurado.
- **Sin servidor ni duplicación.** No hay que mantener un servidor de base de
  datos ni una segunda copia de los datos; los archivos de la TLC son la única
  fuente de verdad.
