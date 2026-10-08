#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

import taxi_db


def remove_database(path: Path) -> None:
    for candidate in (path, path.with_name(path.name + ".wal")):
        candidate.unlink(missing_ok=True)


def build(target: Path, sources: dict[str, str] | None = None) -> dict:
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    remove_database(target)

    con = taxi_db.connect(sources=sources)
    con.execute("SET preserve_insertion_order = false")
    con.execute(f"ATTACH '{target}' AS store")

    start = time.perf_counter()
    con.execute(taxi_db.read_sql("build/materialize.sql"))
    con.execute("USE store")
    con.execute(taxi_db.read_sql("views/trips_clean.sql"))
    con.execute("CHECKPOINT store")
    seconds = time.perf_counter() - start

    rows = con.execute("SELECT count(*) FROM store.main.trips").fetchone()[0]
    con.execute("USE memory")
    con.execute("DETACH store")
    con.close()

    return {"rows": rows, "seconds": seconds, "size_mib": target.stat().st_size / 1024 / 1024}


def main() -> int:
    parser = argparse.ArgumentParser(description="Materializa los viajes en una base DuckDB.")
    parser.add_argument(
        "--output", type=Path, default=taxi_db.DATABASE_PATH,
        help=f"archivo de destino (por defecto: {taxi_db.DATABASE_PATH.relative_to(taxi_db.PROJECT_ROOT)})",
    )
    args = parser.parse_args()

    result = build(args.output)
    print(f"Base creada: {args.output}")
    print(f"  viajes        : {result['rows']:,}")
    print(f"  tiempo        : {result['seconds']:.1f} s")
    print(f"  tamaño        : {result['size_mib']:.1f} MiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
