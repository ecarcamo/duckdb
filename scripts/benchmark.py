#!/usr/bin/env python3
import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

import duckdb

import build_database
import taxi_db

QUERIES = {
    "Q1": ("Conteo por tipo", "06_benchmark/01_count_by_type.sql"),
    "Q2": ("Volumen mensual", "04_eda/01_monthly_volume.sql"),
    "Q3": ("Hora y día de la semana", "04_eda/02_hour_weekday.sql"),
    "Q4": ("Percentiles del viaje", "04_eda/03_trip_profile.sql"),
    "Q5": ("Medio de pago", "04_eda/08_payment_mix.sql"),
    "Q6": ("Zonas principales (1 join)", "04_eda/07_top_pickup_zones.sql"),
    "Q7": ("Aeropuertos (2 joins)", "04_eda/10_airport_trips.sql"),
    "Q8": ("Un solo día (filtro selectivo)", "06_benchmark/02_single_day.sql"),
}

SCALES = {
    "1_month": (
        "1 mes (ene 2026)",
        {
            "yellow": "data/raw/yellow/2026/yellow_tripdata_2026-01.parquet",
            "green": "data/raw/green/2026/green_tripdata_2026-01.parquet",
        },
    ),
    "year_2026": (
        "Año 2026",
        {
            "yellow": "data/raw/yellow/2026/*.parquet",
            "green": "data/raw/green/2026/*.parquet",
        },
    ),
    "all_years": ("Todos los años", dict(taxi_db.DEFAULT_SOURCES)),
}

BENCHMARK_DIR = taxi_db.PROCESSED_DIR / "benchmark"
RESULTS_DIR = taxi_db.PROJECT_ROOT / "docs" / "06_benchmark"


def time_query(con: duckdb.DuckDBPyConnection, sql: str) -> float:
    start = time.perf_counter()
    con.execute(sql).fetchall()
    return time.perf_counter() - start


def source_files(sources: dict[str, str]) -> list[Path]:
    files = []
    for pattern in sources.values():
        files += sorted(taxi_db.PROJECT_ROOT.glob(pattern))
    return files


def run_scale(key: str, runs: int) -> tuple[dict, list[dict]]:
    label, sources = SCALES[key]
    files = source_files(sources)
    database = BENCHMARK_DIR / f"{key}.duckdb"

    print(f"\n=== {label} ===")
    built = build_database.build(database, sources)
    print(f"  tabla materializada: {built['rows']:,} viajes en {built['seconds']:.1f} s ({built['size_mib']:.0f} MiB)")

    build_row = {
        "scale": key,
        "scale_label": label,
        "files": len(files),
        "rows": built["rows"],
        "parquet_mib": round(sum(f.stat().st_size for f in files) / 1024 / 1024, 1),
        "table_mib": round(built["size_mib"], 1),
        "build_seconds": round(built["seconds"], 2),
    }

    connections = {
        "parquet": taxi_db.connect(sources=sources),
        "table": taxi_db.connect(database, read_only=True, views=False),
    }

    rows = []
    for query_id, (description, name) in QUERIES.items():
        sql = taxi_db.read_sql(name)
        for strategy, con in connections.items():
            first = time_query(con, sql)
            timings = [time_query(con, sql) for _ in range(runs)]
            rows.append({
                "scale": key,
                "scale_label": label,
                "rows": built["rows"],
                "query": query_id,
                "description": description,
                "sql_file": name,
                "strategy": strategy,
                "first_seconds": round(first, 4),
                "median_seconds": round(statistics.median(timings), 4),
                "min_seconds": round(min(timings), 4),
                "max_seconds": round(max(timings), 4),
                "runs": runs,
            })
            print(f"  {query_id} {strategy:8s} primera {first:7.3f} s   mediana {statistics.median(timings):7.3f} s")

    for con in connections.values():
        con.close()
    return build_row, rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, builds: list[dict], results: list[dict]) -> None:
    lines = [
        "# Resultados del benchmark",
        "",
        "Archivo generado por `scripts/benchmark.py`. Tiempos en segundos. «Mediana» es la mediana de",
        f"{results[0]['runs']} ejecuciones repetidas, medidas después de una primera ejecución que se reporta",
        "aparte. La aceleración es tiempo con Parquet dividido entre tiempo con la tabla materializada.",
        "",
        "## Datos y materialización",
        "",
        "| Escala | Archivos | Viajes | Parquet (MiB) | Tabla DuckDB (MiB) | Tiempo de materialización (s) |",
        "|---|---|---|---|---|---|",
    ]
    for b in builds:
        lines.append(
            f"| {b['scale_label']} | {b['files']} | {b['rows']:,} | {b['parquet_mib']:,.1f} | "
            f"{b['table_mib']:,.1f} | {b['build_seconds']:.2f} |"
        )

    index = {(r["scale"], r["query"], r["strategy"]): r for r in results}
    for b in builds:
        lines += [
            "",
            f"## {b['scale_label']} ({b['rows']:,} viajes)",
            "",
            "| Consulta | Parquet: mediana | Tabla: mediana | Aceleración | Parquet: primera | Tabla: primera |",
            "|---|---|---|---|---|---|",
        ]
        for query_id, (description, _) in QUERIES.items():
            parquet = index[(b["scale"], query_id, "parquet")]
            table = index[(b["scale"], query_id, "table")]
            lines.append(
                f"| {query_id} {description} | {parquet['median_seconds']:.3f} | {table['median_seconds']:.3f} | "
                f"{parquet['median_seconds'] / table['median_seconds']:.1f}× | "
                f"{parquet['first_seconds']:.3f} | {table['first_seconds']:.3f} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key, value in row.items():
            try:
                row[key] = int(value)
            except ValueError:
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compara consultas sobre archivos Parquet contra una tabla materializada en DuckDB."
    )
    parser.add_argument("--runs", type=int, default=5, help="ejecuciones repetidas por consulta (por defecto: 5)")
    parser.add_argument(
        "--scales", nargs="+", choices=list(SCALES), default=list(SCALES),
        help="escalas a evaluar (por defecto: todas)",
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="regenera results.md a partir de los CSV existentes sin volver a medir",
    )
    args = parser.parse_args()

    if args.report_only:
        write_markdown(
            RESULTS_DIR / "results.md",
            read_csv(RESULTS_DIR / "builds.csv"),
            read_csv(RESULTS_DIR / "results.csv"),
        )
        return 0

    builds, results = [], []
    for key in args.scales:
        build_row, rows = run_scale(key, args.runs)
        builds.append(build_row)
        results += rows

    write_csv(RESULTS_DIR / "builds.csv", builds)
    write_csv(RESULTS_DIR / "results.csv", results)
    write_markdown(RESULTS_DIR / "results.md", builds, results)
    print(f"\nResultados en {RESULTS_DIR.relative_to(taxi_db.PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
