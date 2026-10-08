# Ejercicio 6 — Parquet frente a tablas DuckDB

Notebook ejecutado: [notebooks/06_benchmark.ipynb](../notebooks/06_benchmark.ipynb).
Scripts: [scripts/build_database.py](../scripts/build_database.py) y
[scripts/benchmark.py](../scripts/benchmark.py).
Resultados generados: [docs/06_benchmark/results.md](06_benchmark/results.md),
[results.csv](06_benchmark/results.csv) y [builds.csv](06_benchmark/builds.csv).

## 6.1 Consulta directa sobre Parquet

Es la estrategia usada en los Ejercicios 3 a 5: una conexión de DuckDB en memoria
con las vistas `trips` y `trips_clean`, que leen los archivos de `data/raw/` en
cada consulta. No hay copia de los datos.

## 6.2 Tabla materializada

`scripts/build_database.py` crea `data/processed/taxi.duckdb` con:

- la tabla `trips`: copia de la vista `trips` (todas las columnas unificadas de
  amarillos y verdes, con `taxi_type`, `source_year` y `source_month`);
- la tabla `zones`: copia de `taxi_zone_lookup.csv`;
- la vista `trips_clean`: la misma definición de `sql/views/trips_clean.sql`,
  ahora sobre la tabla.

El SQL de la transformación está en `sql/build/materialize.sql`:

```sql
CREATE OR REPLACE TABLE store.main.trips AS
SELECT *
FROM memory.main.trips;

CREATE OR REPLACE TABLE store.main.zones AS
SELECT *
FROM memory.main.zones;
```

Como la tabla y la vista se llaman igual en ambas estrategias (`trips`,
`trips_clean`, `zones`), **el texto de cada consulta es exactamente el mismo**;
solo cambia la conexión. El notebook comprueba que el resultado de una consulta
es idéntico en las dos.

```bash
docker compose exec lab python scripts/build_database.py
```

```text
Base creada: /workspace/data/processed/taxi.duckdb
  viajes        : 71,870,407
  tiempo        : 7.0 s
  tamaño        : 1970.8 MiB
```

## 6.3 y 6.8 Consultas del benchmark

Seis consultas se tomaron tal cual del análisis exploratorio y dos se agregaron
para cubrir los extremos (conteo trivial y filtro muy selectivo):

| Id | Consulta | Archivo | Qué ejercita |
|---|---|---|---|
| Q1 | Conteo por tipo | `sql/06_benchmark/01_count_by_type.sql` | Recorrido mínimo; Parquet puede responder con metadatos |
| Q2 | Volumen mensual | `sql/04_eda/01_monthly_volume.sql` | Filtro de limpieza + `GROUP BY` + `count(DISTINCT)` |
| Q3 | Hora y día de la semana | `sql/04_eda/02_hour_weekday.sql` | Funciones de fecha y 336 grupos |
| Q4 | Percentiles del viaje | `sql/04_eda/03_trip_profile.sql` | 9 percentiles exactos (`quantile_cont`): ordenamiento pesado |
| Q5 | Medio de pago | `sql/04_eda/08_payment_mix.sql` | `CASE` + función de ventana |
| Q6 | Zonas principales | `sql/04_eda/07_top_pickup_zones.sql` | `JOIN` con zonas + ventana + `row_number` |
| Q7 | Aeropuertos | `sql/04_eda/10_airport_trips.sql` | Dos `JOIN` y clasificación |
| Q8 | Un solo día | `sql/06_benchmark/02_single_day.sql` | Filtro selectivo por fecha (`2026-01-15`) |

## 6.4 a 6.6 Procedimiento

`scripts/benchmark.py` repite el experimento en tres cantidades de datos. Las
tres incluyen enero de 2026, así que Q8 devuelve el mismo resultado en todas:

| Escala | Archivos | Viajes |
|---|---|---|
| 1 mes (enero 2026) | 2 | 3,765,161 |
| Año 2026 (enero a agosto) | 16 | 30,040,469 |
| Todos los años (2024 + 2026) | 40 | 71,870,407 |

Para cada escala:

1. Crea `data/processed/benchmark/<escala>.duckdb` con la misma función de
   `build_database.py` y mide el tiempo de materialización y el tamaño.
2. Abre una conexión Parquet (vistas apuntando a los archivos de esa escala) y
   una conexión a la base materializada en modo `read_only`.
3. Para cada consulta y cada estrategia ejecuta una primera vez (tiempo
   «primera») y luego 5 veces más; se reporta la **mediana** de esas 5, además
   del mínimo y el máximo en el CSV. Las dos estrategias se alternan consulta por
   consulta para que ninguna se beneficie de un orden fijo.

Ambiente: Intel Core i9-13980HX (32 hilos), 15 GiB de RAM, disco NVMe, DuckDB
1.5.5 dentro del contenedor `lab`, `memory_limit = 4GB`, 32 hilos.

```bash
docker compose exec lab python scripts/benchmark.py            # 5 repeticiones, unos 6 minutos
docker compose exec lab python scripts/benchmark.py --runs 3 --scales 1_month
docker compose exec lab python scripts/benchmark.py --report-only
```

## 6.7 Resultados

### Materialización

| Escala | Parquet (MiB) | Tabla DuckDB (MiB) | Tabla / Parquet | Tiempo de materialización |
|---|---|---|---|---|
| 1 mes | 62.1 | 102.3 | 1.65× | 0.90 s |
| Año 2026 | 495.7 | 816.3 | 1.65× | 3.01 s |
| Todos los años | 1,171.7 | 1,972.0 | 1.68× | 7.46 s |

### Tiempos de consulta (mediana, segundos)

| Consulta | 1 mes: Parquet | 1 mes: tabla | Acel. | 2026: Parquet | 2026: tabla | Acel. | Todos: Parquet | Todos: tabla | Acel. |
|---|---|---|---|---|---|---|---|---|---|
| Q1 Conteo por tipo | 0.006 | 0.002 | 2.4× | 0.009 | 0.008 | 1.1× | 0.014 | 0.019 | 0.7× |
| Q2 Volumen mensual | 0.126 | 0.039 | 3.2× | 0.320 | 0.251 | 1.3× | 0.664 | 0.540 | 1.2× |
| Q3 Hora y día | 0.155 | 0.043 | 3.6× | 0.380 | 0.264 | 1.4× | 0.809 | 0.576 | 1.4× |
| Q4 Percentiles | 0.721 | 0.648 | 1.1× | 5.467 | 5.480 | 1.0× | 16.738 | 15.553 | 1.1× |
| Q5 Medio de pago | 0.136 | 0.055 | 2.5× | 0.349 | 0.429 | 0.8× | 0.709 | 0.925 | 0.8× |
| Q6 Zonas (1 join) | 0.166 | 0.036 | 4.6× | 0.381 | 0.215 | 1.8× | 0.814 | 0.471 | 1.7× |
| Q7 Aeropuertos (2 joins) | 0.182 | 0.049 | 3.7× | 0.481 | 0.326 | 1.5× | 1.004 | 0.757 | 1.3× |
| Q8 Un solo día | 0.017 | 0.002 | 7.8× | 0.028 | 0.003 | 10.0× | 0.046 | 0.004 | 10.8× |

Aceleración = tiempo con Parquet ÷ tiempo con la tabla (mayor que 1 favorece a
la tabla). Los tiempos de la primera ejecución están en
[results.md](06_benchmark/results.md).

## 6.9 Análisis

1. **Con pocos datos la tabla gana por 2.4–4.6×, pero en términos absolutos la
   diferencia es de décimas de segundo.** Con un mes, leer Parquet implica abrir
   los archivos, interpretar sus metadatos, descomprimir ZSTD y alinear los
   esquemas de amarillos y verdes en cada consulta. Ese costo fijo pesa mucho
   cuando la consulta en sí tarda 40 ms. La tabla ya está en el formato interno
   de DuckDB y en su caché de bloques.
2. **Al crecer el volumen la ventaja cae a 1.0–1.8×.** Con 30 y 72 millones de
   viajes el tiempo lo domina el cálculo (agrupaciones con hash, ventanas,
   ordenamiento para percentiles), que es idéntico en las dos estrategias. La
   lectura de Parquet escala bien porque DuckDB procesa en paralelo los grupos
   de filas de los 40 archivos con 32 hilos. Q4 es el caso extremo: los
   percentiles exactos tardan unos 16 s con cualquiera de las dos estrategias.
3. **Los filtros selectivos son donde más conviene materializar (8–11×).** Para
   Q8 la tabla usa *zonemaps* (mínimo y máximo por bloque de 122,880 filas) y
   salta casi todos los bloques. Parquet también guarda estadísticas por grupo de
   filas, pero los archivos de la TLC tienen grupos de 1,048,576 filas (4 por
   archivo amarillo) y la consulta debe abrir el pie de cada archivo. Por eso la
   ventaja **crece** con el número de archivos: 7.8× con 2 archivos y 10.8× con 40.
4. **Hay consultas donde Parquet es igual o más rápido.** Q1 (conteo) con
   Parquet se resuelve casi solo con metadatos y gana con 72 millones de filas
   (0.014 s contra 0.019 s). Q5 fue más lenta con la tabla en las escalas grandes
   (0.8×) de forma consistente (mínimos y máximos sin traslape). La lectura no es
   la causa: un `GROUP BY payment_type` simple sobre `trips_clean` tarda 0.31 s
   con la tabla y 0.50 s con Parquet. La diferencia aparece al combinar el `CASE`
   con la función de ventana, así que depende del plan de ejecución de esa
   consulta y no del almacenamiento.
5. **Primera ejecución contra repetidas.** Las diferencias son pequeñas porque los
   archivos ya estaban en la caché de páginas del sistema operativo (1.2 GiB de
   Parquet y 2 GiB de tabla caben en la memoria). Un escenario con caché fría
   (disco remoto u objeto en S3) penalizaría más a la estrategia que lee más
   bytes; aquí la tabla ocupa 1.7 veces más que el Parquet.
6. **El costo de materializar es bajo pero no nulo.** Copiar 72 millones de
   viajes tardó 7.5 s y requirió 2 GiB adicionales. La tabla queda desactualizada
   cuando llega un archivo nuevo y hay que reconstruirla, y un archivo `.duckdb`
   admite un solo escritor: mientras Metabase lo tiene abierto en modo lectura no
   se puede reconstruir.

## 6.10 ¿Cuándo conviene cada estrategia?

**Consultar Parquet directamente conviene cuando:**

- los datos llegan como archivos nuevos con frecuencia (como aquí, cada mes) y
  se quiere que cada consulta vea el último archivo sin un paso de carga;
- el análisis es exploratorio o de una sola vez, y el tiempo de materializar no
  se recupera;
- las consultas recorren todo el conjunto con agregaciones pesadas: la tabla
  apenas mejora 1.0–1.4×;
- el espacio importa o los datos son compartidos por varias herramientas
  (Parquet es un formato abierto que leen pandas, Spark, Polars, etc.);
- se necesita que varios procesos lean a la vez sin bloqueos.

**Materializar una tabla DuckDB conviene cuando:**

- las mismas consultas se repiten muchas veces, como en un tablero (Ejercicio 7),
  y cada consulta es corta: con volúmenes pequeños la tabla es 2–5× más rápida;
- hay filtros selectivos (por fecha, zona o proveedor) que aprovechan los
  *zonemaps*: 8–11× más rápido;
- se quiere guardar transformaciones costosas ya resueltas (unificación de
  esquemas, limpieza, columnas derivadas o tablas de resumen);
- una herramienta externa necesita un esquema estable y no debe depender de
  rutas de archivos (Metabase se conecta a `taxi.duckdb`);
- los datos cambian poco, de modo que reconstruir la tabla es un paso
  ocasional y automatizable (`scripts/build_database.py`).

En este proyecto se usan las dos: Parquet directo para explorar e incorporar
años nuevos sin recargar nada, y una tabla materializada, reconstruida con un
comando, para el tablero.
