# Ejercicio 5 — Incorporación de los datos de 2024

Notebook ejecutado: [notebooks/05_incremental.ipynb](../notebooks/05_incremental.ipynb).
Consultas: [sql/05_incremental/](../sql/05_incremental/).

## 5.1 Cambio en el sistema de descarga

Como el script ya recibía el año como parámetro desde el Ejercicio 2, incorporar
2024 fue un cambio de una línea en `scripts/download_data.py`:

```diff
-DEFAULT_YEARS = (2026,)
+DEFAULT_YEARS = (2024, 2026)
```

Los datos se obtienen de la fuente original (CloudFront de la TLC) con la misma
lógica: consulta `HEAD` de cada mes, descarga atómica sobre `.part` y
verificación de `Content-Length`. También se puede descargar un año sin cambiar
el código con `--years 2024`.

## 5.2 a 5.4 Ejecución

```bash
docker compose exec lab python scripts/download_data.py
```

```text
RESUMEN
  años          : 2024, 2026
  descargados   : 24
  ya existían   : 16
  no publicados : 8
      yellow 2026-09 ... yellow 2026-12, green 2026-09 ... green 2026-12
  fallidos      : 0
```

- Se descargaron los 24 archivos de 2024 (12 amarillos de 47.6 a 61.4 MiB y 12
  verdes de 1.2 a 1.4 MiB; 677 MiB en total).
- Los 16 archivos de 2026 aparecen como «ya existe, se omite»: se conservaron
  sin volver a pedirlos al servidor (5.2 y 5.3).
- Una segunda ejecución, incluida en el notebook, reporta `descargados: 0` y
  `ya existían: 40`.

## 5.5 Verificación de los archivos nuevos

1. **Integridad:** `python scripts/download_data.py --verify` comparó los 40
   archivos contra el tamaño publicado y abrió sus metadatos Parquet:
   `verificados: 40`, `incompletos: 0`.
2. **Inventario** (`01_inventory_by_year.sql`, solo metadatos):

   | Tipo | Año | Archivos | Filas |
   |---|---|---|---|
   | yellow | 2024 | 12 | 41,169,720 |
   | yellow | 2026 | 8 | 29,703,355 |
   | green | 2024 | 12 | 660,218 |
   | green | 2026 | 8 | 337,114 |

3. **Cobertura** (`02_missing_months.sql`): 2024 tiene los 12 meses para ambos
   tipos; a 2026 le faltan septiembre a diciembre, que la TLC aún no publica.
4. **Esquema** (`03_schema_by_year.sql`, `PIVOT` sobre `parquet_schema`): los
   archivos de 2024 tienen las mismas columnas que los de 2026, excepto
   `cbd_congestion_fee` (el cargo de congestión empezó a cobrarse en enero de
   2025) y `request_source` (desde junio de 2026). `07_type_conflicts.sql` del
   Ejercicio 3 no encontró columnas con tipos distintos entre años.

## 5.6 Consulta conjunta de 2024 y 2026

La vista `trips` ya lee `data/raw/*/*/*.parquet`, así que los nuevos archivos
aparecen sin tocarla. Registros por año (`04_rows_by_year.sql`):

| Tipo | Año | Crudos | Limpios | % descartado |
|---|---|---|---|---|
| yellow | 2024 | 41,169,720 | 39,688,329 | 3.60 |
| yellow | 2026 | 29,703,355 | 28,593,831 | 3.74 |
| green | 2024 | 660,218 | 621,093 | 5.93 |
| green | 2026 | 337,114 | 322,606 | 4.30 |

En total la vista expone 71,870,407 viajes en 40 archivos.

Comparación con los mismos meses (`05_year_comparison.sql`, enero a agosto,
detectados automáticamente como los meses presentes en todos los años):

| Tipo | Año | Viajes/día | Monto prom. | Distancia mediana | Duración mediana | % tarjeta | % efectivo | % con cargo CBD |
|---|---|---|---|---|---|---|---|---|
| yellow | 2024 | 104,507 | 28.32 | 1.80 | 12.7 | 75.9 | 13.8 | 0.0 |
| yellow | 2026 | 117,670 | 30.20 | 1.92 | 14.1 | 65.6 | 9.1 | 72.4 |
| green | 2024 | 1,709 | 23.79 | 1.96 | 11.9 | 67.8 | 27.8 | 0.0 |
| green | 2026 | 1,328 | 25.47 | 2.14 | 13.3 | 65.6 | 19.4 | 8.5 |

Primeras observaciones: los amarillos crecieron 12.6 % en viajes diarios
mientras los verdes cayeron 22 %; el monto promedio subió cerca de 7 % en ambos;
los viajes duran más (12.7 → 14.1 minutos de mediana) y el efectivo perdió peso.
El análisis completo de la evolución se hace en el Ejercicio 8, con 2025.

## 5.7 ¿Las consultas anteriores necesitan cambios?

Se ejecutaron sin modificar las 31 consultas de los Ejercicios 3 y 4 sobre el
conjunto ampliado (ver tabla en el notebook): **todas terminaron sin error**,
porque ninguna menciona archivos ni años concretos y todas leen las vistas o el
patrón `data/raw/*/*/*.parquet`. La más lenta fue `04_eda/03_trip_profile.sql`
(14.6 s, por los percentiles exactos sobre 40 millones de filas).

Dos consultas sí se ajustaron porque su **resultado** perdía sentido al mezclar
años:

| Consulta | Problema con 2024 + 2026 | Cambio |
|---|---|---|
| `03_exploration/13_pickup_date_range.sql` | Contaba viajes «anteriores a 2026», con el año fijo en el texto; todos los viajes de 2024 caían ahí. | Compara cada viaje con el año de su archivo (`source_year`) y agrupa por tipo y año. |
| `04_eda/11_cbd_congestion_fee.sql` | Agrupaba solo por mes: enero de 2024 (sin cargo CBD) y enero de 2026 se sumaban y el porcentaje bajaba a la mitad. | Agrupa por año y mes. |

El resto de las consultas del Ejercicio 4 describen el conjunto completo; para
comparar años basta agregar `source_year` al `GROUP BY`, como hacen las
consultas de este ejercicio.

Con la versión corregida de `13_pickup_date_range.sql` se ve que los archivos de
2024 también tienen fechas imposibles: 49 viajes amarillos con fecha anterior a
2024 (desde 2002) y 7 posteriores (hasta junio de 2026). La regla «el abordaje
debe caer en el mes del archivo» de `trips_clean` los descarta sin cambios.

## 5.8 Consultas de validación

| Archivo | Objetivo | Fuente | Resultado |
|---|---|---|---|
| `01_inventory_by_year.sql` | Archivos y filas por tipo y año | `parquet_file_metadata` | 40 archivos, 71.9 millones de filas |
| `02_missing_months.sql` | Meses esperados contra presentes | `glob` | 2024 completo; 2026 sin sep–dic |
| `03_schema_by_year.sql` | Columnas presentes por tipo y año | `parquet_schema` + `PIVOT` | Solo difieren `cbd_congestion_fee` y `request_source` |
| `04_rows_by_year.sql` | Viajes crudos y limpios por año | vistas `trips` y `trips_clean` | 3.6–5.9 % descartado por año |
| `05_year_comparison.sql` | Comparar años con los mismos meses | vista `trips_clean` + `glob` | Ver tabla de 5.6 |
| `06_monthly_trend.sql` | Viajes por día mes a mes | vista `trips_clean` | Gráfica en el notebook |

## 5.9 Características del diseño que permiten agregar archivos

1. **Convención de rutas.** Cada archivo vive en
   `data/raw/<tipo>/<año>/<nombre-original>.parquet`. El tipo y el año se
   derivan de la ruta, no de una lista mantenida a mano.
2. **Globs en lugar de listas de archivos.** Las vistas leen
   `data/raw/<tipo>/*/*.parquet`; un archivo nuevo en la carpeta forma parte de
   la consulta en la siguiente ejecución.
3. **`union_by_name = true` y `UNION ALL BY NAME`.** Las columnas se alinean
   por nombre; una columna que no existe en algunos años (`cbd_congestion_fee`)
   se rellena con `NULL` en lugar de romper la consulta. La vista `trips` usa
   `SELECT *` con `RENAME`, así que una columna nueva de la TLC aparece sola.
4. **Metadatos del archivo como columnas.** `source_year` y `source_month` salen
   del nombre del archivo (`filename = true`), por lo que las reglas de calidad y
   las comparaciones no dependen de años escritos en el SQL.
5. **Capa de vistas única.** Las reglas de unificación (`trips`) y limpieza
   (`trips_clean`) están en un solo lugar (`sql/views/`); las consultas de
   análisis no repiten rutas ni reglas.
6. **Descarga idempotente y parametrizada.** Agregar un año es cambiar
   `DEFAULT_YEARS` o pasar `--years`; volver a ejecutar el script nunca repite
   descargas y `--verify` confirma la integridad.
7. **Consultas que detectan el periodo.** `02_missing_months.sql` y
   `05_year_comparison.sql` calculan los años y meses disponibles a partir de
   los archivos, así que siguen siendo válidas al agregar 2025.
