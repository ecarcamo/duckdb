# Ejercicio 1 — Preparación del ambiente

## 1.1 y 1.2 Fork, clonación y arranque

- Fork del repositorio del docente (`menene/duckdb`) en `ecarcamo/duckdb`.
- Clonación del fork y registro del repositorio del docente como `upstream`:

```bash
git clone https://github.com/ecarcamo/duckdb.git
cd duckdb
git remote add upstream https://github.com/menene/duckdb.git
git fetch upstream
git switch -c lab8
```

- Construcción y arranque de los servicios en segundo plano:

```bash
docker compose up --build -d
```

La primera construcción tarda algunos minutos porque descarga la imagen de Python,
las dependencias de `requirements.txt`, Metabase (`metabase.jar`) y el driver de
DuckDB para Metabase.

## 1.3 Verificación de los servicios

| Verificación | Comando | Resultado obtenido |
|---|---|---|
| Contenedores en ejecución | `docker compose ps` | `lab8-lab` y `lab8-metabase` en estado `Up` |
| JupyterLab responde | `curl -s -o /dev/null -w "%{http_code}" localhost:8888/lab` | `200` |
| Metabase responde | `curl -s localhost:3000/api/health` | `{"status":"ok"}` |
| DuckDB disponible en Python | `docker compose exec lab python -c "import duckdb; print(duckdb.__version__)"` | `1.5.5` |
| Driver de DuckDB en Metabase | `docker compose exec metabase ls /home/metabase/plugins` | `duckdb.metabase-driver.jar` |

Salida de `docker compose ps` al momento de la verificación:

```text
NAME            IMAGE             SERVICE    STATUS          PORTS
lab8-lab        duckdb-lab        lab        Up 16 minutes   127.0.0.1:8888->8888/tcp
lab8-metabase   duckdb-metabase   metabase   Up 16 minutes   127.0.0.1:3000->3000/tcp
```

## 1.4 Herramientas disponibles

### Servicio `lab` (imagen `python:3.11.14-slim`)

| Herramienta | Versión | Uso en el laboratorio |
|---|---|---|
| Python | 3.11.14 | Lenguaje de los scripts y notebooks |
| DuckDB (módulo de Python) | 1.5.5 | Motor analítico: consultas sobre Parquet y base materializada |
| JupyterLab | 4.6.4 | Notebooks de exploración y análisis (puerto 8888, sin token) |
| pandas | 3.0.6 | Recibir resultados pequeños de DuckDB para mostrarlos o graficarlos |
| PyArrow | 25.0.1 | Lectura de metadatos Parquet e intercambio de datos con DuckDB |
| Matplotlib | 3.11.2 | Gráficas dentro de los notebooks |
| Requests | 2.34.2 | Descarga de archivos desde el servidor de la TLC |
| nbconvert / nbformat | 7.17.1 / 5.11.1 | Ejecutar notebooks desde la línea de comandos |
| curl | sistema | Pruebas rápidas de conectividad |

No se incluye el cliente de línea de comandos de DuckDB: todas las consultas se
ejecutan desde Python (`duckdb.connect()`), ya sea en scripts o en notebooks.

### Servicio `metabase` (imagen `eclipse-temurin:21-jre-jammy`)

| Herramienta | Versión | Uso en el laboratorio |
|---|---|---|
| Java (Temurin) | 21.0.12 | Ejecuta Metabase |
| Metabase | v0.63.19 | Tablero de indicadores (puerto 3000) |
| Driver DuckDB para Metabase | 1.5.5.0 | Permite a Metabase leer archivos `.duckdb` |

La versión del driver (1.5.5.0) está alineada con la del módulo de Python
(`duckdb==1.5.5`), de modo que ambos servicios leen el mismo formato de archivo.

### Volúmenes compartidos

| Ruta en el equipo | Ruta en `lab` | Ruta en `metabase` |
|---|---|---|
| `./data` | `/workspace/data` | `/workspace/data` |
| `./notebooks` | `/workspace/notebooks` | — |
| `./scripts` | `/workspace/scripts` | — |
| `./sql` | `/workspace/sql` | — |
| `./docs` | `/workspace/docs` | — |

Ambos contenedores ven los datos en la misma ruta (`/workspace/data`), por lo que
una base creada en el servicio `lab` puede abrirse desde Metabase sin copiarla.

## Propósito de cada directorio

| Directorio | Propósito |
|---|---|
| `data/raw/` | Archivos Parquet originales tal como los publica la TLC, organizados por `tipo/año`. Nunca se modifican: son la fuente de verdad y se pueden volver a descargar. Están excluidos de Git. |
| `data/processed/` | Productos derivados de los datos crudos: la base materializada `taxi.duckdb`, la base del benchmark y archivos temporales. Se regeneran con los scripts y también están excluidos de Git. |
| `notebooks/` | Notebooks de Jupyter con la exploración, el análisis y sus resultados ejecutados. Son la evidencia del análisis. |
| `scripts/` | Código Python reutilizable y ejecutable desde la terminal: descarga, construcción de la base y benchmark. Es la parte automatizable del flujo. |
| `sql/` | Consultas SQL del laboratorio en archivos separados, para que estén versionadas y se puedan ejecutar desde los notebooks, los scripts o Metabase. |
| `docs/` | Documentación de cada ejercicio: objetivos, consultas, resultados, decisiones, tablas del benchmark y evidencia del tablero. |
| `Dockerfile` | Imagen del ambiente de análisis (Python, DuckDB, JupyterLab). |
| `metabase.Dockerfile` | Imagen de Metabase sobre Debian con el driver de DuckDB. |
| `docker-compose.yml` | Define los dos servicios, sus puertos y los volúmenes compartidos. |
| `README.md` | Punto de entrada: cómo levantar el ambiente, descargar los datos y reproducir el trabajo. |

La separación entre `raw` y `processed` refleja una regla importante: los datos
crudos son inmutables y todo lo demás se deriva de ellos con código versionado.

## 1.6 ¿Por qué importa un ambiente reproducible?

1. **Mismos resultados en cualquier equipo.** Las versiones de Python, DuckDB,
   pandas y Metabase están fijadas en `requirements.txt` y en los Dockerfile. Una
   consulta que funciona en una computadora funciona igual en la de cualquier
   integrante o en la del catedrático.
2. **Compatibilidad entre herramientas.** El formato de archivo de DuckDB cambia
   entre versiones; fijar `duckdb==1.5.5` junto con el driver 1.5.5.0 garantiza que
   la base creada desde Python se pueda abrir en Metabase.
3. **Arranque inmediato.** Un integrante nuevo solo necesita Docker y Git: no
   instala Java, Python ni librerías a mano, y no hay diferencias de sistema
   operativo.
4. **Separación entre código y datos.** El código vive en Git y los datos se
   obtienen con un script; así cualquier persona puede reconstruir exactamente el
   mismo conjunto de datos desde la fuente oficial sin subir gigabytes al
   repositorio.
5. **Trazabilidad.** Si un resultado cambia, se puede saber si fue por el código
   (historial de Git), por los datos (archivos nuevos de la TLC) o por el ambiente
   (versiones fijadas), en lugar de adivinar.
6. **Aislamiento.** Los puertos se publican solo en `127.0.0.1` y los contenedores
   no alteran el sistema del equipo anfitrión.
