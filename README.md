# Lab 8 - DuckDB

Repositorio base del laboratorio 8 del curso **CC3084 - Data Science**
(Universidad del Valle de Guatemala, Ciclo 2, 2026).

Este es el repositorio **proporcionado por el docente**. Contiene la estructura
del proyecto, el ambiente de ejecucion basado en Docker y un script que descarga
los datos de **2026**. Todo lo demas debe ser construido por cada equipo.

## Trabajo con fork

El laboratorio se desarrolla y se entrega sobre un **fork** de este repositorio.
No se trabaja directamente sobre el repositorio del docente.

1. Realice un fork de este repositorio:
   <https://github.com/menene/duckdb>

2. Clone **su propio fork** (no el del docente):

   ```bash
   git clone https://github.com/<su-usuario>/duckdb.git
   cd duckdb
   ```

3. Opcional, para recibir correcciones publicadas por el docente:

   ```bash
   git remote add upstream https://github.com/menene/duckdb.git
   git fetch upstream
   ```

Realice commits frecuentes y descriptivos: el historial del repositorio es parte
de la evaluacion. **La entrega del laboratorio es la URL de su fork.**

## Estructura

```text
duckdb/
|
+-- data/
|   +-- raw/
|   +-- processed/
|
+-- notebooks/
|
+-- scripts/
|
+-- sql/
|
+-- docs/
|
+-- Dockerfile
+-- metabase.Dockerfile
+-- docker-compose.yml
+-- README.md
```

## Requisitos

- Docker, con Docker Compose
- Git

La primera construccion del ambiente descarga varios cientos de MB y puede
tardar algunos minutos.

Considere el espacio en disco: las imagenes de Docker ocupan unos 3 GB y los
datos de los tres anios del laboratorio superan 1.5 GB, a los que se suma la
base materializada del Ejercicio 6. Se recomienda tener al menos 10 GB libres.

## Datos

El repositorio incluye `scripts/download_data.py`, que descarga los archivos de
2026 publicados por la TLC (`--help` muestra las opciones disponibles). Los
archivos se guardan en `data/raw/<tipo>/<anio>/`.

La TLC publica cada mes con varias semanas de atraso, por lo que los ultimos
meses de 2026 todavia no existen. El script consulta al servidor que meses estan
publicados, de modo que vuelve a ejecutarse sin problema conforme aparezcan
nuevos archivos.

Los datos descargados **no deben incluirse en el repositorio Git**. El archivo
`.gitignore` ya esta configurado para evitarlo.

Fuente de datos: NYC TLC Trip Record Data
<https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>

Dentro de los contenedores, la carpeta `data/` del proyecto esta montada en
`/workspace/data`. Esa es la ruta que deben usar las herramientas que corren
dentro del ambiente, no la ruta de su computadora.

> **Nota sobre DuckDB:** un archivo `.duckdb` admite un solo proceso con permiso
> de escritura a la vez. Si conecta una herramienta externa a su base de datos,
> use el modo de solo lectura (`read_only`) en esa conexion; de lo contrario los
> demas procesos no podran abrir el archivo.

## Material a entregar

Al finalizar, su fork debe contener:

- el codigo fuente modificado y los scripts de descarga;
- las consultas SQL desarrolladas;
- el notebook o notebooks utilizados;
- la documentacion de las consultas;
- los scripts utilizados para los benchmarks;
- el codigo de los indicadores y visualizaciones;
- el tablero o la evidencia del tablero desarrollado;
- este `README.md`, completado segun la siguiente seccion.

Los archivos de datos descargados **no** deben incluirse.

---

# Documentacion del equipo

Las siguientes secciones deben ser completadas por cada equipo. El README final
debe permitir que una persona que no participo en el desarrollo pueda levantar el
ambiente, descargar los datos, ejecutar el analisis, reproducir los benchmarks y
generar los resultados principales.

## Como levantar el ambiente

Requisitos: Docker con Docker Compose, Git y al menos 10 GB libres en disco.

1. Clonar el fork y entrar al directorio:

   ```bash
   git clone https://github.com/ecarcamo/duckdb.git
   cd duckdb
   git switch lab8
   ```

2. Construir las imágenes y levantar los servicios en segundo plano:

   ```bash
   docker compose up --build -d
   ```

3. Verificar que ambos servicios estén en ejecución:

   ```bash
   docker compose ps
   curl -s localhost:3000/api/health
   docker compose exec lab python -c "import duckdb; print(duckdb.__version__)"
   ```

   Se espera ver `lab8-lab` y `lab8-metabase` en estado `Up`, la respuesta
   `{"status":"ok"}` de Metabase y la versión `1.5.5` de DuckDB.

4. Abrir las herramientas en el navegador:

   - JupyterLab: <http://localhost:8888> (sin token).
   - Metabase: <http://localhost:3000> (la primera vez pide crear una cuenta de
     administrador local).

5. Para detener el ambiente sin perder la configuración de Metabase:

   ```bash
   docker compose down
   ```

Todos los comandos de Python del proyecto se ejecutan dentro del servicio `lab`
con `docker compose exec lab ...`, cuyo directorio de trabajo es `/workspace`.
El detalle de la verificación, las herramientas disponibles y el propósito de
cada directorio está en [docs/01_environment.md](docs/01_environment.md).

## Como descargar los datos

El script `scripts/download_data.py` descarga los viajes de taxis amarillos y
verdes publicados por la TLC y la tabla de zonas:

```bash
docker compose exec lab python scripts/download_data.py
```

| Opción | Efecto |
|---|---|
| (sin opciones) | Descarga los años de `DEFAULT_YEARS` (2024 y 2026) para ambos tipos de taxi. |
| `--years 2024 2026` | Descarga los años indicados. |
| `--taxi yellow` o `--taxi green` | Limita la descarga a un tipo de taxi. |
| `--verify` | Compara cada archivo local contra el tamaño publicado y valida que el Parquet sea legible. |

Los archivos quedan en `data/raw/<tipo>/<año>/<tipo>_tripdata_<año>-<mes>.parquet`
y la tabla de zonas en `data/raw/zones/taxi_zone_lookup.csv`. Un archivo que ya
existe no se vuelve a descargar, de modo que el comando puede repetirse cuando
la TLC publique meses nuevos. Para confirmar que el conjunto está completo:

```bash
docker compose exec lab python scripts/download_data.py --verify
```

Para agregar un año se edita `DEFAULT_YEARS` o se usa `--years`; las consultas
no cambian porque leen todos los archivos de `data/raw/` (ver
[docs/05_incremental.md](docs/05_incremental.md)).

El análisis del script original, los cambios y la verificación están en
[docs/02_download.md](docs/02_download.md).

## Como ejecutar el analisis

Las consultas están en `sql/`, una por archivo, y se ejecutan desde los
notebooks de `notebooks/` con el módulo `scripts/taxi_db.py`, que abre DuckDB
con la raíz del proyecto como directorio de trabajo y crea las vistas
`yellow_raw`, `green_raw`, `trips`, `trips_clean` y `zones` sobre los archivos
Parquet (`sql/views/`).

Los notebooks se pueden abrir en JupyterLab (<http://localhost:8888>) o
ejecutar completos desde la terminal; el resultado queda guardado en el mismo
archivo:

```bash
docker compose exec -w /workspace/notebooks lab jupyter nbconvert --to notebook --execute --inplace 03_exploration.ipynb
```

| Notebook | Ejercicio | Documentación |
|---|---|---|
| `03_exploration.ipynb` | 3. Consultas directas sobre Parquet | [docs/03_exploration.md](docs/03_exploration.md) |
| `04_eda.ipynb` | 4. Análisis exploratorio | [docs/04_eda.md](docs/04_eda.md) |
| `05_incremental.ipynb` | 5. Incorporación de 2024 | [docs/05_incremental.md](docs/05_incremental.md) |

## Como reproducir los benchmarks

<!-- TODO (Ejercicio 6) -->

## Como generar los resultados principales

<!-- TODO -->
