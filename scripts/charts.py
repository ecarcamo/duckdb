import matplotlib.pyplot as plt

TAXI_COLORS = {"yellow": "#eda100", "green": "#008300"}
TAXI_LABELS = {"yellow": "Amarillo", "green": "Verde"}
YEAR_COLORS = {2024: "#2a78d6", 2025: "#eb6834", 2026: "#1baf7a"}
SEQUENTIAL_MAP = "Blues"
WEEKDAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def apply_style() -> None:
    plt.rcParams.update({
        "figure.figsize": (10, 4.5),
        "figure.dpi": 100,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#8a8984",
        "axes.labelcolor": "#52514e",
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#e4e3df",
        "grid.linewidth": 0.8,
        "xtick.color": "#52514e",
        "ytick.color": "#52514e",
        "lines.linewidth": 2,
        "lines.markersize": 6,
        "legend.frameon": False,
    })


def thousands(ax, axis: str = "y") -> None:
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:,.0f}"))
