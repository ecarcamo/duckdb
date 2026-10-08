#!/usr/bin/env python3
"""Descarga los archivos Parquet del NYC TLC Trip Record Data.

Descarga los registros de viajes de taxis amarillos (yellow) y verdes (green)
de los años configurados en DEFAULT_YEARS (o los indicados con --years), junto
con la tabla de zonas de taxi de la TLC.

Fuente oficial de los datos:
    https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Uso:
    python scripts/download_data.py                        # años por defecto
    python scripts/download_data.py --taxi yellow
    python scripts/download_data.py --years 2026
    python scripts/download_data.py --verify               # revisa completitud

Los archivos se guardan en:
    data/raw/<tipo>/<año>/<nombre-original>.parquet
    data/raw/zones/taxi_zone_lookup.csv

Comportamiento:
  - La TLC publica cada mes con varias semanas de atraso. El script consulta al
    servidor qué meses están publicados en lugar de suponerlos.
  - Un archivo que ya existe localmente no se vuelve a descargar.
  - La descarga se hace sobre un nombre temporal y solo se renombra al
    terminar, de modo que una interrupción no deja archivos .parquet a medias.
  - Con --verify se compara cada archivo local contra el tamaño publicado por
    el servidor y se abren sus metadatos Parquet para confirmar que es legible.
"""

import argparse
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq
import requests

DEFAULT_YEARS = (2024, 2025, 2026)
TAXI_TYPES = ("yellow", "green")
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONES_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
RAW_DIR = Path("data/raw")
ZONES_PATH = RAW_DIR / "zones" / "taxi_zone_lookup.csv"

TIMEOUT = 60
ATTEMPTS = 3
RETRY_DELAY = 2
CHUNK_SIZE = 1024 * 1024
TEMP_SUFFIX = ".part"


def file_name(taxi: str, year: int, month: int) -> str:
    """Nombre del archivo publicado por la TLC, p. ej. yellow_tripdata_2026-01.parquet."""
    return f"{taxi}_tripdata_{year}-{month:02d}.parquet"


def file_url(taxi: str, year: int, month: int) -> str:
    """URL completa del archivo Parquet mensual."""
    return f"{BASE_URL}/{file_name(taxi, year, month)}"


def local_path(taxi: str, year: int, month: int) -> Path:
    """Ruta local donde se guarda el archivo."""
    return RAW_DIR / taxi / str(year) / file_name(taxi, year, month)


def remote_size(url: str) -> int | None:
    """Tamaño publicado del archivo en bytes, o None si no está publicado."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException:
            response = None
        if response is not None and response.ok:
            return int(response.headers.get("Content-Length", 0))
        if attempt < ATTEMPTS:
            time.sleep(RETRY_DELAY * attempt)
    return None


def format_size(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GiB"


def download_file(url: str, target: Path) -> int:
    """Descarga `url` en `target`. Devuelve la cantidad de bytes escritos."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + TEMP_SUFFIX)

    last_error = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT) as response:
                response.raise_for_status()
                expected = int(response.headers.get("Content-Length", 0))
                written = 0
                with temp.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            handle.write(chunk)
                            written += len(chunk)
            if written == 0:
                raise requests.RequestException("el servidor devolvió un archivo vacío")
            if expected and written != expected:
                raise requests.RequestException(
                    f"descarga incompleta ({written} de {expected} bytes)"
                )
            temp.replace(target)
            return written
        except requests.RequestException as error:
            last_error = error
            temp.unlink(missing_ok=True)
            if attempt < ATTEMPTS:
                print(f"      intento {attempt}/{ATTEMPTS} fallido ({error}); reintentando")

    raise requests.RequestException(f"no se pudo descargar {url}: {last_error}")


def parquet_rows(path: Path) -> int | None:
    """Cantidad de filas según los metadatos Parquet, o None si el archivo no es legible."""
    try:
        return pq.ParquetFile(path).metadata.num_rows
    except Exception:
        return None


def new_summary() -> dict:
    return {
        "downloaded": 0,
        "skipped": 0,
        "verified": 0,
        "unpublished": [],
        "failed": [],
        "invalid": [],
    }


def sync(taxi: str, year: int, verify: bool) -> dict:
    """Descarga (o verifica) todos los meses publicados de un tipo de taxi y un año."""
    print(f"\n=== {taxi.upper()} {year} ===")
    summary = new_summary()

    for month in range(1, 13):
        label = f"{year}-{month:02d}"
        target = local_path(taxi, year, month)
        url = file_url(taxi, year, month)
        exists = target.exists() and target.stat().st_size > 0

        if exists and not verify:
            print(f"  {label}  ya existe, se omite")
            summary["skipped"] += 1
            continue

        size = remote_size(url)
        if size is None:
            if exists:
                print(f"  {label}  existe localmente pero ya no aparece publicado")
                summary["invalid"].append(label)
            else:
                print(f"  {label}  aún no publicado por la TLC")
                summary["unpublished"].append(label)
            continue

        if exists:
            local_size = target.stat().st_size
            rows = parquet_rows(target)
            if local_size != size or rows is None:
                print(
                    f"  {label}  INCOMPLETO: local {format_size(local_size)}, "
                    f"servidor {format_size(size)}, legible: {rows is not None}"
                )
                summary["invalid"].append(label)
            else:
                print(f"  {label}  verificado ({format_size(local_size)}, {rows:,} filas)")
                summary["verified"] += 1
            summary["skipped"] += 1
            continue

        print(f"  {label}  descargando {format_size(size)}...")
        try:
            written = download_file(url, target)
        except requests.RequestException as error:
            print(f"  {label}  ERROR: {error}")
            summary["failed"].append(label)
        else:
            print(f"  {label}  listo ({format_size(written)}) -> {target}")
            summary["downloaded"] += 1
            if verify:
                summary["verified"] += 1

    return summary


def sync_zones() -> None:
    """Descarga la tabla de zonas de taxi si todavía no existe."""
    if ZONES_PATH.exists() and ZONES_PATH.stat().st_size > 0:
        print(f"\nZonas: {ZONES_PATH} ya existe, se omite")
        return
    written = download_file(ZONES_URL, ZONES_PATH)
    print(f"\nZonas: listo ({format_size(written)}) -> {ZONES_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descarga los datos de taxis amarillos y verdes del NYC TLC."
    )
    parser.add_argument(
        "--taxi", choices=(*TAXI_TYPES, "all"), default="all",
        help="tipo de taxi a descargar (por defecto: all)",
    )
    parser.add_argument(
        "--years", type=int, nargs="+", default=list(DEFAULT_YEARS),
        help=f"años a descargar (por defecto: {' '.join(map(str, DEFAULT_YEARS))})",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="compara los archivos locales contra el servidor y valida que sean Parquet legibles",
    )
    args = parser.parse_args()

    taxis = TAXI_TYPES if args.taxi == "all" else (args.taxi,)

    total = new_summary()
    for year in sorted(set(args.years)):
        for taxi in taxis:
            summary = sync(taxi, year, args.verify)
            for key in ("downloaded", "skipped", "verified"):
                total[key] += summary[key]
            for key in ("unpublished", "failed", "invalid"):
                total[key] += [f"{taxi} {label}" for label in summary[key]]

    try:
        sync_zones()
    except requests.RequestException as error:
        print(f"\nZonas: ERROR: {error}")
        total["failed"].append("zones")

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  años          : {', '.join(map(str, sorted(set(args.years))))}")
    print(f"  descargados   : {total['downloaded']}")
    print(f"  ya existían   : {total['skipped']}")
    if args.verify:
        print(f"  verificados   : {total['verified']}")
        print(f"  incompletos   : {len(total['invalid'])}")
        if total["invalid"]:
            print(f"      {', '.join(total['invalid'])}")
    print(f"  no publicados : {len(total['unpublished'])}")
    if total["unpublished"]:
        print(f"      {', '.join(total['unpublished'])}")
    print(f"  fallidos      : {len(total['failed'])}")
    if total["failed"]:
        print(f"      {', '.join(total['failed'])}")
    print("=" * 60)

    return 1 if total["failed"] or total["invalid"] else 0


if __name__ == "__main__":
    sys.exit(main())
