import os
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROCESSED_DIR / "taxi.duckdb"
VIEW_SCRIPTS = ("views/raw.sql", "views/trips.sql", "views/trips_clean.sql", "views/zones.sql")
MEMORY_LIMIT = "4GB"
DEFAULT_SOURCES = {
    "yellow": "data/raw/yellow/*/*.parquet",
    "green": "data/raw/green/*/*.parquet",
}


def read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


def configure(con: duckdb.DuckDBPyConnection) -> None:
    PROCESSED_DIR.joinpath("tmp").mkdir(parents=True, exist_ok=True)
    try:
        con.execute("SET enable_progress_bar = false")
    except duckdb.InvalidInputException:
        pass
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute(f"SET temp_directory = '{PROCESSED_DIR / 'tmp'}'")


def create_views(con: duckdb.DuckDBPyConnection, sources: dict[str, str] | None = None) -> None:
    for script in VIEW_SCRIPTS:
        sql = read_sql(script)
        for taxi, pattern in (sources or {}).items():
            sql = sql.replace(DEFAULT_SOURCES[taxi], pattern)
        con.execute(sql)


def connect(
    database: str | Path = ":memory:",
    read_only: bool = False,
    views: bool = True,
    sources: dict[str, str] | None = None,
):
    os.chdir(PROJECT_ROOT)
    con = duckdb.connect(str(database), read_only=read_only)
    configure(con)
    if views:
        create_views(con, sources)
    return con


def query(con: duckdb.DuckDBPyConnection, name: str):
    return con.sql(read_sql(name)).df()


def show(con: duckdb.DuckDBPyConnection, name: str):
    print(read_sql(name).strip())
    return query(con, name)
