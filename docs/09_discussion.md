# Ejercicio 9 — Discusión

Las respuestas se apoyan en los resultados de los Ejercicios 1 a 8; entre
paréntesis se indica dónde está cada evidencia.

## 9.1 ¿Qué características de DuckDB resultaron más útiles?

1. **Leer Parquet como si fuera una tabla.** `read_parquet` con globs
   (`data/raw/*/*/*.parquet`) permitió explorar 30 millones de viajes sin un
   paso de carga y, más tarde, 121 millones repartidos en 64 archivos con el
   mismo SQL (Ejercicios 3, 5 y 8).
2. **`union_by_name` y `UNION ALL BY NAME`.** Los archivos amarillos y verdes
   tienen columnas distintas y las columnas cambian con los años
   (`cbd_congestion_fee` desde 2025, `request_source` desde junio de 2026).
   Alinear por nombre evitó escribir un esquema a mano y que la incorporación de
   un año rompiera las consultas.
3. **Funciones de metadatos.** `glob`, `parquet_metadata`,
   `parquet_file_metadata` y `parquet_schema` contaron archivos, filas y
   columnas en milisegundos sin leer los datos. Con ellas se construyeron las
   validaciones de completitud y de esquema (consultas 01–07 del Ejercicio 3 y
   01–03 del Ejercicio 5).
4. **SQL analítico expresivo.** `SUMMARIZE` hizo el perfil de calidad de 21
   columnas en una línea; `GROUP BY ALL`, `FILTER`, `UNPIVOT`, `PIVOT`,
   `quantile_cont`, `approx_quantile`, `SELECT * EXCLUDE ... RENAME` y las
   ventanas con `lag` mantuvieron las consultas cortas y legibles.
5. **Ejecución fuera de memoria.** Con `memory_limit = 4GB` y `temp_directory`,
   DuckDB procesó 121 millones de filas en un equipo con 5 GB libres. Cuando una
   consulta no cupo (duplicados agrupando por 26 columnas) bastó con cambiar el
   enfoque (agrupar por `hash` de la fila).
6. **Base de datos en un archivo.** `CREATE TABLE ... AS SELECT` materializó
   121 millones de viajes en 12 segundos, y el mismo archivo `.duckdb` lo abrió
   Metabase sin servidor de por medio (Ejercicios 6 y 7).
7. **Integración con Python.** `con.sql(...).df()` entrega resultados ya
   agregados a pandas para graficar, sin cargar las filas originales.

## 9.2 Ventajas y limitaciones de consultar Parquet directamente

**Ventajas observadas**

- Cero tiempo de carga: el dato nuevo está disponible en cuanto el archivo
  llega a `data/raw/`; agregar 2024 y 2025 no requirió tocar el SQL.
- Lectura selectiva: formato columnar, compresión ZSTD y estadísticas por grupo
  de filas. Contar los 30 millones de filas de 2026 por metadatos tardó 0.01 s.
- Ocupa menos espacio: 1.9 GiB de Parquet frente a 3.3 GiB de la tabla
  materializada con los mismos datos.
- Con agregaciones que recorren todo el conjunto el rendimiento es casi igual
  al de una tabla (aceleración de la tabla de solo 1.0–1.4× en Q2, Q3 y Q4 con
  72 millones de viajes, Ejercicio 6).
- Formato abierto: los mismos archivos los leen pandas, PyArrow o Spark.

**Limitaciones observadas**

- Costo fijo por consulta: abrir archivos, leer sus pies y alinear esquemas.
  Con un mes de datos la tabla fue entre 2.4 y 4.6 veces más rápida en la
  mayoría de las consultas.
- Filtros selectivos más lentos: buscar un solo día fue 8–11 veces más lento
  que en la tabla, porque los grupos de filas de la TLC son grandes (1,048,576
  filas) y hay que abrir el pie de cada archivo.
- El esquema depende de lo que publique la fuente: columnas nuevas, nombres que
  difieren entre tipos (`tpep_*` / `lpep_*`) y semántica que cambia sin aviso
  (registros *flex fare*, proveedor 7 sin hora de descenso, tarifas negativas en
  2025). Todo eso hay que resolverlo en las vistas, en cada consulta.
- Las rutas son relativas al proceso que consulta: Metabase, que corre en otro
  contenedor, no podía reutilizar las vistas del proyecto tal cual; por eso se
  le dio una base materializada.

## 9.3 Ventajas y limitaciones de las tablas materializadas

**Ventajas**

- Consultas cortas y repetidas más rápidas (2–5× con volúmenes pequeños) y
  filtros selectivos hasta 11× más rápidos gracias a los *zonemaps*.
- Un esquema estable y ya unificado para herramientas externas: Metabase solo
  ve `trips`, `trips_clean` y `zones`.
- Las transformaciones costosas quedan resueltas una vez.

**Limitaciones**

- Duplican los datos y ocupan más: 1.65–1.7 veces el tamaño del Parquet
  (3.3 GiB con tres años).
- Quedan desactualizadas: cada año nuevo exigió volver a ejecutar
  `build_database.py` (12 s con 121 millones de viajes).
- Un solo escritor por archivo: para reconstruir la base hubo que detener
  Metabase, que la tenía abierta en modo lectura.
- La ventaja casi desaparece en consultas dominadas por cálculo: los
  percentiles exactos (Q4) tardaron unos 16 s en ambas estrategias, y Q5 fue
  incluso más lenta con la tabla.

## 9.4 Ventajas frente a cargar todo con pandas

- **Memoria.** Los 121 millones de viajes ocupan 1.9 GiB comprimidos en Parquet;
  en un DataFrame de pandas con 26 columnas (fechas, flotantes y textos)
  requerirían varias veces la memoria libre del equipo (5 GB). DuckDB nunca
  materializó las filas en Python: a pandas solo llegaron resultados de decenas
  o cientos de filas.
- **Velocidad.** DuckDB usa los 32 hilos del procesador y lee solo las columnas
  necesarias; pandas lee archivos completos y opera en un solo hilo. Las agregaciones
  del benchmark sobre 72 millones de filas tardaron alrededor de 1 segundo o
  menos, salvo los percentiles exactos (Ejercicio 6).
- **Fuera de memoria.** DuckDB puede usar disco temporal cuando una operación no
  cabe; pandas simplemente falla.
- **Incrementalidad.** Agregar un año fue copiar archivos; con pandas habría que
  volver a cargar y concatenar todo.
- **SQL versionable y reutilizable.** Las mismas consultas de `sql/` se usaron en
  notebooks, en el benchmark y en Metabase.
- pandas sigue siendo útil al final de la cadena: para dar formato a tablas
  pequeñas y graficar con Matplotlib.

## 9.5 Características que permiten incorporar datos con cambios mínimos

- La descarga recibe los años como parámetro (`DEFAULT_YEARS` o `--years`):
  2024 y 2025 se agregaron cambiando una línea.
- La descarga es idempotente: omite los archivos existentes, escribe de forma
  atómica (`.part`) y `--verify` confirma la integridad.
- Hay una convención de rutas (`data/raw/<tipo>/<año>/`) y vistas que leen globs.
- `union_by_name`, `UNION ALL BY NAME` y `SELECT *` con `RENAME` absorben las
  columnas nuevas.
- El año y el mes salen del nombre del archivo (`source_year`, `source_month`),
  sin años escritos en el SQL.
- Las consultas de validación y comparación detectan solas qué años y meses hay.
- La materialización y el tablero se regeneran con un comando cada uno.

Resultado: al pasar de un año a tres, las 37 consultas anteriores y las 12 del
tablero se ejecutaron sin errores; solo dos se ajustaron (en el Ejercicio 5)
porque su resultado mezclaba años: una tenía 2026 escrito en el SQL y otra
agrupaba solo por mes.

## 9.6 ¿Qué debería automatizarse en producción?

1. **Detección y descarga programada** de meses nuevos (la TLC publica con
   semanas de atraso), por ejemplo un trabajo mensual que ejecute
   `download_data.py` y luego `--verify`.
2. **Validación automática de cada archivo nuevo**: esquema contra el esperado
   (`03_schema_by_year.sql`), conteo de filas, porcentaje descartado por
   `trips_clean` y alertas cuando cambie bruscamente. La anomalía de 2025 (8.3 %
   descartado frente a 3.7 %) y el proveedor 7 sin hora de descenso se
   encontraron a mano; deberían disparar una alerta.
3. **Reconstrucción incremental de la tabla** (insertar solo los meses nuevos en
   lugar de copiar todo) y coordinación con Metabase, que hoy hay que detener.
4. **Actualización del tablero** después de cada carga (`metabase_dashboard.py`)
   y caché de las preguntas.
5. **Pruebas de regresión de las consultas**: ejecutar todas las de `sql/` y
   comparar resultados de referencia, como se hizo manualmente en los Ejercicios
   5 y 8.
6. **Benchmark periódico** para decidir con datos cuándo conviene materializar.

## 9.7 Decisiones de diseño importantes para la reproducibilidad

- **Ambiente en Docker con versiones fijas** (Python 3.11.14, DuckDB 1.5.5 y
  driver de Metabase alineado).
- **Datos fuera de Git** (`.gitignore`) y obtenidos siempre de la fuente oficial
  con un script; las credenciales también fuera de Git (`.env`).
- **Datos crudos inmutables** (`data/raw`) y todo lo derivado regenerable
  (`data/processed`).
- **SQL en archivos versionados**, uno por consulta, ejecutados igual desde
  notebooks, scripts y Metabase.
- **Rutas relativas a la raíz del proyecto** (`taxi_db.connect()` fija el
  directorio de trabajo), de modo que el mismo SQL funciona desde cualquier lugar.
- **Reglas de limpieza en una sola vista** (`trips_clean`), documentadas y
  corregidas en un commit identificable cuando se encontró un error.
- **Notebooks guardados con sus resultados** y ejecutables de principio a fin
  con `nbconvert`; muestras con semilla fija (`REPEATABLE (42)`).
- **Benchmark y tablero generados por código**, con sus resultados exportados
  (`docs/06_benchmark/`, `docs/07_dashboard/`).
- **Commits por ejercicio**, de modo que el historial muestra cómo creció el
  sistema.

## 9.8 ¿Qué se aprende que no sería evidente con datos pequeños?

- **La calidad cambia con el tiempo y con el proveedor.** Con un mes no se ve que
  los registros *flex fare* pasaron de 4 % a 28 %, que en 2025 un proveedor
  reportó 1.9 millones de tarifas negativas, ni que un proveedor nuevo no registra
  la hora de descenso. Una regla de limpieza razonable puede eliminar segmentos
  completos (367 mil viajes del proveedor 7) sin que se note.
- **El esquema también evoluciona.** Aparecen columnas (`cbd_congestion_fee`,
  `request_source`) y hay que diseñar para eso desde el inicio.
- **Las conclusiones dependen del periodo.** Con 2024 y 2026 parecía un
  crecimiento continuo de los amarillos; con 2025 se vio que fue un salto en 2025
  y una estabilización en 2026.
- **El rendimiento no escala de forma lineal ni uniforme.** Una consulta que con
  un mes tarda 0.7 s tardó 37 s con 121 millones de filas (percentiles exactos);
  las aproximadas (`approx_quantile`) se vuelven necesarias. La estrategia más
  rápida con poco volumen (tabla, 4×) casi no ayuda con mucho volumen.
- **La memoria es una restricción de diseño.** Una consulta que agrupaba por
  todas las columnas agotó 4 GB con 30 millones de filas; hubo que replantearla.
  Con datos pequeños cualquier enfoque funciona.
- **Los extremos son muchos aunque sean un porcentaje pequeño.** Un 0.03 % de
  velocidades imposibles son miles de registros; con datos pequeños no aparecen
  o parecen casos aislados.
- **La totalidad hay que verificarla.** Con muchos archivos, un error de red
  transitorio hizo que 9 meses publicados parecieran inexistentes en la primera
  descarga; sin una verificación explícita el conjunto habría quedado incompleto
  sin aviso.
