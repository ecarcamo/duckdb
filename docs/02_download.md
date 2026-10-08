# Ejercicio 2 — Sistema de descarga

## 2.1 Análisis del script original

El script entregado (`scripts/download_data.py`) ya resolvía parte del problema:

- Construía la URL de cada mes con el patrón de la TLC
  (`<tipo>_tripdata_<año>-<mes>.parquet`).
- Recorría los meses 1 a 12 y hacía una petición `HEAD` para saber si el mes
  estaba publicado.
- Omitía archivos existentes con tamaño mayor que cero.
- Descargaba sobre un archivo `.part` y lo renombraba al terminar, con tres
  reintentos.

Las partes que impedían usarlo como sistema de descarga del laboratorio eran:

| Problema | Consecuencia | Cambio necesario |
|---|---|---|
| El año estaba fijo en la constante `ANIO = 2026`, también en el docstring y en la descripción de la línea de comandos. | Para agregar 2024 y 2025 habría que copiar el script o editar la constante cada vez, y no se podían bajar varios años en una sola ejecución. | Parametrizar el año: lista `DEFAULT_YEARS` y opción `--years`. |
| Una respuesta `HEAD` fallida se interpretaba de inmediato como «mes no publicado». | Un error transitorio del servidor hace que un mes publicado se reporte como inexistente. Ocurrió en la primera ejecución: solo se descargaron 7 de los 16 archivos. | Reintentar la consulta `HEAD` con espera progresiva antes de concluir que el mes no existe. |
| La descarga solo validaba que el archivo no estuviera vacío. | Una conexión cortada a mitad de la respuesta podía producir un Parquet truncado. | Comparar los bytes escritos contra `Content-Length`. |
| No había manera de comprobar los archivos ya descargados. | La omisión de existentes se basa solo en «existe y pesa más de 0 bytes»; no hay forma de saber si el conjunto local está completo. | Modo `--verify`: compara cada archivo contra el tamaño publicado y abre sus metadatos Parquet. |
| No descargaba la tabla de zonas de la TLC. | Los campos `PULocationID` y `DOLocationID` son códigos sin nombre. | Descargar `taxi_zone_lookup.csv` en `data/raw/zones/`. |

## 2.2 a 2.4 Cambios realizados

- **Años configurables.** `DEFAULT_YEARS = (2026,)` define el conjunto por
  defecto del laboratorio y `--years 2024 2025 2026` permite indicar otros. Las
  funciones `file_name`, `file_url` y `local_path` reciben el año como parámetro.
- **Tipos de taxi.** Se mantienen `yellow` y `green` (`--taxi yellow|green|all`).
- **Estructura de directorios.** Cada archivo se guarda en
  `data/raw/<tipo>/<año>/<nombre-original>.parquet`, que es la estructura que
  ya definía el proyecto y la que usan las consultas
  (`data/raw/*/*/*.parquet`). La tabla de zonas va en
  `data/raw/zones/taxi_zone_lookup.csv`.
- **Sin descargas repetidas.** Antes de cualquier petición de red se revisa si
  el archivo ya existe con tamaño mayor que cero; si existe se omite y no se
  consulta al servidor.
- **Robustez.** Reintentos con espera para `HEAD`, verificación de
  `Content-Length` al descargar y escritura atómica mediante `.part`.
- **Verificación.** `--verify` consulta el servidor para cada mes, compara el
  tamaño local con el publicado y lee el número de filas de los metadatos
  Parquet con PyArrow. Un archivo distinto o ilegible se reporta como
  «incompleto» y el script termina con código 1.
- **Identificadores en inglés.** Las funciones y constantes se renombraron al
  inglés (`file_url`, `local_path`, `remote_size`, `download_file`, `sync`); los
  mensajes al usuario siguen en español.

## 2.5 Ejecución

```bash
docker compose exec lab python scripts/download_data.py
```

Primera ejecución (con el `HEAD` original sin reintentos): se descargaron 7
archivos y 9 meses publicados se reportaron por error como «no publicados».
Después de agregar los reintentos, la segunda ejecución omitió los 7 existentes
y descargó los 9 faltantes:

```text
RESUMEN
  años          : 2026
  descargados   : 9
  ya existían   : 7
  no publicados : 8
      yellow 2026-09 ... yellow 2026-12, green 2026-09 ... green 2026-12
  fallidos      : 0
```

Una tercera ejecución no descargó nada (`descargados: 0`, `ya existían: 16`),
lo que confirma que el script no repite descargas.

Archivos obtenidos:

| Tipo | Meses | Archivos | Tamaño |
|---|---|---|---|
| yellow 2026 | enero a agosto | 8 | 488 MiB |
| green 2026 | enero a agosto | 8 | 8 MiB |
| zonas | — | 1 | 12 KiB |

## 2.7 ¿Cómo se determinó que el conjunto está completo?

Se usaron tres criterios independientes:

1. **Meses publicados según la fuente.** El script pregunta al servidor por los
   12 meses de cada tipo. En la fecha de descarga (8 de octubre de 2026) la TLC
   tenía publicados enero a agosto de 2026 para ambos tipos; septiembre a
   diciembre devuelven `403`, que es la respuesta del servidor para objetos que
   no existen. Por lo tanto se esperan 16 archivos (8 yellow + 8 green).
2. **Tamaño exacto.** `--verify` compara cada archivo local con el
   `Content-Length` publicado. Los 16 coinciden byte por byte.
3. **Legibilidad.** `--verify` abre los metadatos Parquet de cada archivo y lee
   su número de filas, lo que falla si el archivo está truncado.

```bash
docker compose exec lab python scripts/download_data.py --verify
```

```text
=== YELLOW 2026 ===
  2026-01  verificado (61.2 MiB, 3,724,889 filas)
  2026-02  verificado (56.0 MiB, 3,399,866 filas)
  2026-03  verificado (64.7 MiB, 3,952,451 filas)
  2026-04  verificado (61.8 MiB, 3,831,240 filas)
  2026-05  verificado (66.5 MiB, 4,090,836 filas)
  2026-06  verificado (62.4 MiB, 3,837,248 filas)
  2026-07  verificado (58.8 MiB, 3,530,109 filas)
  2026-08  verificado (56.3 MiB, 3,336,716 filas)

=== GREEN 2026 ===
  2026-01  verificado (968.4 KiB, 40,272 filas)
  2026-02  verificado (899.2 KiB, 37,373 filas)
  2026-03  verificado (1.0 MiB, 44,208 filas)
  2026-04  verificado (1.0 MiB, 44,238 filas)
  2026-05  verificado (1.1 MiB, 44,921 filas)
  2026-06  verificado (1.0 MiB, 44,163 filas)
  2026-07  verificado (994.4 KiB, 41,252 filas)
  2026-08  verificado (983.9 KiB, 40,687 filas)

RESUMEN
  verificados   : 16
  incompletos   : 0
  no publicados : 8
  fallidos      : 0
```

La continuidad de los meses (no hay huecos entre enero y agosto) y un volumen
mensual estable (entre 3.3 y 4.1 millones de viajes amarillos y entre 37 mil y
45 mil verdes) también descartan archivos faltantes o vacíos. La cuenta de
registros se vuelve a comprobar con DuckDB en el Ejercicio 3.
