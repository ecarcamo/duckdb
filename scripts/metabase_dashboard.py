#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

import requests

import taxi_db

METABASE_URL = os.environ.get("MB_URL", "http://metabase:3000")
DATABASE_NAME = "Taxis NYC (DuckDB)"
DATABASE_FILE = "/workspace/data/processed/taxi.duckdb"
COLLECTION_NAME = "Lab 8 - Taxis NYC"
DASHBOARD_NAME = "Lab 8 - Viajes de taxi en Nueva York"
DASHBOARD_DESCRIPTION = (
    "Indicadores de los viajes de taxis amarillos y verdes de Nueva York (TLC), "
    "calculados con DuckDB sobre la tabla materializada data/processed/taxi.duckdb."
)
EXPORT_DIR = taxi_db.PROJECT_ROOT / "docs" / "07_dashboard"

TAXI_SERIES = {
    "yellow": {"title": "Amarillo", "color": "#EDA100"},
    "green": {"title": "Verde", "color": "#008300"},
}
YEAR_SERIES = {
    "2024": {"color": "#2A78D6"},
    "2025": {"color": "#EB6834"},
    "2026": {"color": "#1BAF7A"},
}


def line(dimensions: list[str], metrics: list[str], y_title: str, **extra) -> dict:
    settings = {
        "graph.dimensions": dimensions,
        "graph.metrics": metrics,
        "graph.y_axis.title_text": y_title,
        "graph.x_axis.title_text": "",
        "series_settings": TAXI_SERIES if "taxi_type" in dimensions else {},
    }
    settings.update(extra)
    return settings


INDICATORS = [
    {
        "key": "kpi_trips",
        "name": "Viajes analizados",
        "question": "¿Cuántos viajes válidos contiene el conjunto de datos?",
        "sql": "07_indicators/01_kpi_summary.sql",
        "display": "scalar",
        "settings": {"scalar.field": "trips", "scalar.compact_primary_number": True},
        "layout": (0, 0, 8, 3),
    },
    {
        "key": "kpi_revenue",
        "name": "Ingreso total (millones de USD)",
        "question": "¿Cuánto dinero movieron esos viajes?",
        "sql": "07_indicators/01_kpi_summary.sql",
        "display": "scalar",
        "settings": {"scalar.field": "revenue_musd"},
        "layout": (8, 0, 8, 3),
    },
    {
        "key": "kpi_ticket",
        "name": "Monto promedio por viaje (USD)",
        "question": "¿Cuánto paga en promedio un pasajero por viaje?",
        "sql": "07_indicators/01_kpi_summary.sql",
        "display": "scalar",
        "settings": {"scalar.field": "avg_ticket"},
        "layout": (16, 0, 8, 3),
    },
    {
        "key": "trips_per_day",
        "name": "I1 · Viajes por día según mes",
        "question": "¿Cómo evoluciona la demanda diaria de cada tipo de taxi?",
        "sql": "07_indicators/02_trips_per_day.sql",
        "display": "line",
        "settings": line(["month", "taxi_type"], ["trips_per_day"], "Viajes por día (escala log)", **{"graph.y_axis.scale": "log"}),
        "layout": (0, 3, 12, 7),
    },
    {
        "key": "revenue",
        "name": "I2 · Ingreso mensual (millones de USD)",
        "question": "¿Cuánto ingreso genera cada mes y qué parte aporta cada tipo de taxi?",
        "sql": "07_indicators/03_monthly_revenue.sql",
        "display": "bar",
        "settings": line(["month", "taxi_type"], ["revenue_musd"], "Millones de USD", **{"stackable.stack_type": "stacked"}),
        "layout": (12, 3, 12, 7),
    },
    {
        "key": "avg_ticket",
        "name": "I3 · Monto promedio por viaje (USD)",
        "question": "¿Está subiendo lo que paga un pasajero por viaje?",
        "sql": "07_indicators/04_avg_ticket.sql",
        "display": "line",
        "settings": line(["month", "taxi_type"], ["avg_ticket"], "USD por viaje"),
        "layout": (0, 10, 12, 7),
    },
    {
        "key": "tip_pct",
        "name": "I4 · Propina con tarjeta (% de la tarifa)",
        "question": "¿Qué tan generosas son las propinas y cambian con el tiempo?",
        "sql": "07_indicators/07_tip_pct.sql",
        "display": "line",
        "settings": line(["month", "taxi_type"], ["tip_pct_of_fare"], "% de la tarifa"),
        "layout": (12, 10, 12, 7),
    },
    {
        "key": "hourly",
        "name": "I5 · Distribución de viajes por hora (%)",
        "question": "¿En qué horas se concentra la demanda de cada tipo de taxi?",
        "sql": "07_indicators/05_hourly_demand.sql",
        "display": "line",
        "settings": line(["hour", "taxi_type"], ["pct_of_trips"], "% de los viajes del tipo", **{"graph.x_axis.scale": "ordinal"}),
        "layout": (0, 17, 12, 7),
    },
    {
        "key": "speed",
        "name": "I6 · Velocidad mediana por hora (mph)",
        "question": "¿A qué horas el tráfico hace más lentos los viajes?",
        "sql": "07_indicators/10_speed_by_hour.sql",
        "display": "line",
        "settings": line(
            ["hour"], ["median_mph"], "Millas por hora",
            **{
                "graph.x_axis.scale": "ordinal",
                "series_settings": {"median_mph": {"title": "Velocidad mediana", "color": "#2A78D6"}},
            },
        ),
        "layout": (12, 17, 12, 7),
    },
    {
        "key": "payment",
        "name": "I7 · Medio de pago por año (%)",
        "question": "¿Cómo pagan los pasajeros y está cambiando la forma de pago?",
        "sql": "07_indicators/06_payment_mix.sql",
        "display": "bar",
        "settings": {
            "graph.dimensions": ["year", "payment"],
            "graph.metrics": ["pct_of_trips"],
            "stackable.stack_type": "stacked",
            "graph.y_axis.title_text": "% de los viajes",
            "graph.x_axis.title_text": "",
            "series_settings": {
                "Tarjeta": {"color": "#2A78D6"},
                "Efectivo": {"color": "#1BAF7A"},
                "Flex fare": {"color": "#EB6834"},
                "Otro o nulo": {"color": "#B4B2A9"},
            },
        },
        "layout": (0, 24, 8, 7),
    },
    {
        "key": "airport",
        "name": "I8 · Peso de los aeropuertos (%)",
        "question": "¿Qué parte de los viajes y del ingreso viene de los aeropuertos?",
        "sql": "07_indicators/08_airport_share.sql",
        "display": "bar",
        "settings": {
            "graph.dimensions": ["year"],
            "graph.metrics": ["pct_trips", "pct_revenue"],
            "graph.y_axis.title_text": "%",
            "graph.x_axis.title_text": "",
            "graph.show_values": True,
            "series_settings": {
                "pct_trips": {"title": "% de viajes", "color": "#9FC4EE"},
                "pct_revenue": {"title": "% de ingresos", "color": "#2A78D6"},
            },
        },
        "layout": (8, 24, 8, 7),
    },
    {
        "key": "green_share",
        "name": "I9 · Participación de los taxis verdes (%)",
        "question": "¿Están perdiendo terreno los taxis verdes frente a los amarillos?",
        "sql": "07_indicators/11_green_share.sql",
        "display": "line",
        "settings": {
            "graph.dimensions": ["month"],
            "graph.metrics": ["green_pct"],
            "graph.y_axis.title_text": "% de los viajes",
            "graph.x_axis.title_text": "",
            "series_settings": {"green_pct": {"title": "Taxis verdes", "color": "#008300"}},
        },
        "layout": (16, 24, 8, 7),
    },
    {
        "key": "top_zones",
        "name": "I10 · Zonas con más abordajes",
        "question": "¿Dónde se originan más viajes?",
        "sql": "07_indicators/09_top_zones.sql",
        "display": "row",
        "settings": {
            "graph.dimensions": ["zone"],
            "graph.metrics": ["trips"],
            "graph.show_values": True,
            "graph.x_axis.title_text": "",
            "graph.y_axis.title_text": "Viajes",
            "series_settings": {"trips": {"title": "Viajes", "color": "#2A78D6"}},
        },
        "layout": (0, 31, 12, 8),
    },
    {
        "key": "cbd_fee",
        "name": "I11 · Cargo de congestión CBD (millones de USD)",
        "question": "¿Cuánto recauda el cargo de congestión de Manhattan desde que existe?",
        "sql": "07_indicators/12_cbd_fee.sql",
        "display": "bar",
        "settings": {
            "graph.dimensions": ["month"],
            "graph.metrics": ["cbd_fee_musd"],
            "graph.y_axis.title_text": "Millones de USD",
            "graph.x_axis.title_text": "",
            "series_settings": {"cbd_fee_musd": {"title": "Cargo CBD", "color": "#2A78D6"}},
        },
        "layout": (12, 31, 12, 8),
    },
]


class Metabase:
    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.session = requests.Session()
        api_key = os.environ.get("API_KEY") or os.environ.get("MB_API_KEY")
        if api_key:
            self.session.headers["x-api-key"] = api_key
        else:
            user, password = os.environ.get("MB_USER"), os.environ.get("MB_PASSWORD")
            if not (user and password):
                raise SystemExit("Defina API_KEY en .env, o bien MB_USER y MB_PASSWORD.")
            token = self.request("POST", "/api/session", json={"username": user, "password": password})["id"]
            self.session.headers["X-Metabase-Session"] = token

    def request(self, method: str, path: str, **kwargs):
        response = self.session.request(method, self.url + path, timeout=120, **kwargs)
        if not response.ok:
            raise SystemExit(f"{method} {path} -> {response.status_code}: {response.text[:500]}")
        return response.json() if response.content else None


def ensure_database(mb: Metabase) -> int:
    databases = mb.request("GET", "/api/database")["data"]
    details = {"database_file": DATABASE_FILE, "read_only": True, "old_implicit_casting": True}
    for database in databases:
        if database["name"] == DATABASE_NAME:
            mb.request("PUT", f"/api/database/{database['id']}", json={"details": details})
            return database["id"]
    created = mb.request("POST", "/api/database", json={"engine": "duckdb", "name": DATABASE_NAME, "details": details})
    return created["id"]


def ensure_collection(mb: Metabase) -> int:
    for collection in mb.request("GET", "/api/collection"):
        if collection.get("name") == COLLECTION_NAME and not collection.get("archived"):
            return collection["id"]
    return mb.request("POST", "/api/collection", json={"name": COLLECTION_NAME})["id"]


def collection_items(mb: Metabase, collection_id: int, model: str) -> dict[str, int]:
    items = mb.request("GET", f"/api/collection/{collection_id}/items", params={"models": model})["data"]
    return {item["name"]: item["id"] for item in items}


def upsert_card(mb: Metabase, indicator: dict, database_id: int, collection_id: int, existing: dict[str, int]) -> int:
    payload = {
        "name": indicator["name"],
        "description": indicator["question"],
        "display": indicator["display"],
        "visualization_settings": indicator["settings"],
        "collection_id": collection_id,
        "dataset_query": {
            "type": "native",
            "native": {"query": taxi_db.read_sql(indicator["sql"]), "template-tags": {}},
            "database": database_id,
        },
    }
    if indicator["name"] in existing:
        card_id = existing[indicator["name"]]
        mb.request("PUT", f"/api/card/{card_id}", json=payload)
        return card_id
    return mb.request("POST", "/api/card", json=payload)["id"]


def upsert_dashboard(mb: Metabase, collection_id: int, cards: dict[str, int]) -> int:
    existing = collection_items(mb, collection_id, "dashboard")
    if DASHBOARD_NAME in existing:
        dashboard_id = existing[DASHBOARD_NAME]
    else:
        dashboard_id = mb.request(
            "POST", "/api/dashboard",
            json={"name": DASHBOARD_NAME, "description": DASHBOARD_DESCRIPTION, "collection_id": collection_id},
        )["id"]

    dashcards = []
    for position, indicator in enumerate(INDICATORS, start=1):
        col, row, size_x, size_y = indicator["layout"]
        dashcards.append({
            "id": -position,
            "card_id": cards[indicator["key"]],
            "col": col,
            "row": row,
            "size_x": size_x,
            "size_y": size_y,
            "parameter_mappings": [],
            "visualization_settings": {},
        })
    mb.request(
        "PUT", f"/api/dashboard/{dashboard_id}",
        json={"description": DASHBOARD_DESCRIPTION, "dashcards": dashcards, "width": "full"},
    )
    return dashboard_id


def public_link(mb: Metabase, dashboard_id: int) -> str:
    mb.request("PUT", "/api/setting/enable-public-sharing", json={"value": True})
    uuid = mb.request("POST", f"/api/dashboard/{dashboard_id}/public_link")["uuid"]
    return f"http://localhost:3000/public/dashboard/{uuid}"


def native_query(dataset_query: dict) -> str:
    if "native" in dataset_query:
        return dataset_query["native"]["query"]
    return dataset_query["stages"][0]["native"]


def export_definition(mb: Metabase, dashboard_id: int) -> Path:
    dashboard = mb.request("GET", f"/api/dashboard/{dashboard_id}")
    cards = [
        {
            "name": dashcard["card"]["name"],
            "description": dashcard["card"].get("description"),
            "display": dashcard["card"]["display"],
            "query": native_query(dashcard["card"]["dataset_query"]),
            "visualization_settings": dashcard["card"]["visualization_settings"],
            "layout": {key: dashcard[key] for key in ("col", "row", "size_x", "size_y")},
        }
        for dashcard in sorted(dashboard["dashcards"], key=lambda d: (d["row"], d["col"]))
    ]
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = EXPORT_DIR / "dashboard.json"
    target.write_text(
        json.dumps({"name": dashboard["name"], "description": dashboard["description"], "cards": cards}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea o actualiza el tablero del laboratorio en Metabase.")
    parser.add_argument("--url", default=METABASE_URL, help=f"URL de Metabase (por defecto: {METABASE_URL})")
    parser.add_argument("--public", action="store_true", help="activa el enlace público del tablero")
    args = parser.parse_args()

    mb = Metabase(args.url)
    database_id = ensure_database(mb)
    collection_id = ensure_collection(mb)
    existing = collection_items(mb, collection_id, "card")

    cards = {}
    for indicator in INDICATORS:
        cards[indicator["key"]] = upsert_card(mb, indicator, database_id, collection_id, existing)
        result = mb.request("POST", f"/api/card/{cards[indicator['key']]}/query")
        if result.get("status") != "completed":
            raise SystemExit(f"La tarjeta «{indicator['name']}» falló: {result.get('error')}")
        print(f"  tarjeta lista: {indicator['name']} ({result['row_count']} filas)")

    dashboard_id = upsert_dashboard(mb, collection_id, cards)
    print(f"\nTablero: http://localhost:3000/dashboard/{dashboard_id}")
    if args.public:
        print(f"Enlace público: {public_link(mb, dashboard_id)}")
    print(f"Definición exportada en {export_definition(mb, dashboard_id).relative_to(taxi_db.PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
