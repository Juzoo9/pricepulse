from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _setup_style():
    plt.style.use("dark_background")
    plt.rcParams.update({
        "axes.facecolor": "#1e1e2e",
        "axes.edgecolor": "#6c7086",
        "axes.labelcolor": "#cdd6f4",
        "axes.grid": True,
        "grid.alpha": 0.2,
        "grid.color": "#6c7086",
        "xtick.color": "#6c7086",
        "ytick.color": "#6c7086",
        "lines.linewidth": 2.5,
        "figure.facecolor": "#11111b",
    })


async def generate_price_chart(
    history: list[tuple[datetime, float]], title: str
) -> bytes:
    _setup_style()

    if not history:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(
            0.5, 0.5, "Нет данных для графика",
            ha="center", va="center", color="#6c7086", fontsize=14,
        )
        ax.set_facecolor("#1e1e2e")
    else:
        dates, prices = zip(*history)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, prices, color="#89b4fa", marker="o", markersize=4)

        ax.set_title(title, color="#cdd6f4", fontsize=14, pad=12)
        ax.set_xlabel("Дата", fontsize=11)
        ax.set_ylabel("Цена", fontsize=11)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()

        min_price = min(prices)
        max_price = max(prices)
        padding = (max_price - min_price) * 0.1 or max_price * 0.1 or 10
        ax.set_ylim(min_price - padding, max_price + padding)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()