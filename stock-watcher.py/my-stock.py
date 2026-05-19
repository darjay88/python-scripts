#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Static
from textual.reactive import reactive
from textual import work

import asyncio
import requests
from datetime import datetime

# ============================================
# CONFIG
# ============================================

API_KEY = "d834sb1r01ql4onganfgd834sb1r01ql4ongang0"

TICKERS = [
    "ET",
    "CCL",
    "NCLH",
    "PCG",
    "KEY",
    "CVE",
    "JD",
    "BCS",
    "HDB",
    "IBN",
    "SONY",
    "BBVA",
    "NEO",
    "NET",
    "SOFI",
    "SPY",
]

REFRESH_RATE = 2


# ============================================
# API
# ============================================

def fetch_quote(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY}"

    r = requests.get(url, timeout=5)
    r.raise_for_status()

    data = r.json()

    return {
        "current": data["c"],
        "high": data["h"],
        "low": data["l"],
        "open": data["o"],
        "prev_close": data["pc"],
    }


# ============================================
# HELPERS
# ============================================

def calc_change(current, prev):
    diff = current - prev
    pct = (diff / prev) * 100 if prev else 0
    return diff, pct


def colorize(diff):
    if diff > 0:
        return "green"
    elif diff < 0:
        return "red"
    return "white"


# ============================================
# MAIN APP
# ============================================

class BloombergTerminal(App):

    CSS = """
    Screen {
        background: black;
        color: white;
    }

    Header {
        background: rgb(255,140,0);
        color: black;
    }

    Footer {
        background: rgb(255,140,0);
        color: black;
    }

    #left-panel {
        width: 75%;
        border: solid orange;
    }

    #right-panel {
        width: 25%;
        border: solid orange;
    }

    DataTable {
        height: 1fr;
    }

    Static {
        padding: 1;
    }
    """

    clock = reactive("")

    def compose(self) -> ComposeResult:

        yield Header(show_clock=True)

        with Horizontal():

            with Vertical(id="left-panel"):
                self.table = DataTable()
                yield self.table

            with Vertical(id="right-panel"):
                self.info = Static("Loading...")
                yield self.info

        yield Footer()

    def on_mount(self):

        self.table.add_columns(
            "Ticker",
            "Price",
            "Change",
            "%",
            "High",
            "Low",
        )

        self.set_interval(1, self.update_clock)

        self.load_data()

    def update_clock(self):
        self.clock = datetime.now().strftime("%H:%M:%S")

    @work
    async def load_data(self):

        while True:

            self.table.clear()

            summary_lines = []

            for ticker in TICKERS:

                try:
                    q = fetch_quote(ticker)

                    current = q["current"]
                    prev = q["prev_close"]

                    diff, pct = calc_change(current, prev)

                    color = colorize(diff)

                    arrow = (
                        "▲" if diff > 0 else
                        "▼" if diff < 0 else
                        "■"
                    )

                    self.table.add_row(
                        ticker,
                        f"${current:.2f}",
                        f"[{color}]{arrow} {diff:+.2f}[/{color}]",
                        f"[{color}]{pct:+.2f}%[/{color}]",
                        f"${q['high']:.2f}",
                        f"${q['low']:.2f}",
                    )

                    summary_lines.append(
                        f"[{color}]{ticker:<6} "
                        f"${current:.2f} "
                        f"{pct:+.2f}%[/{color}]"
                    )

                except Exception as e:
                    self.table.add_row(
                        ticker,
                        "ERR",
                        "",
                        "",
                        "",
                        "",
                    )

            self.info.update(
                "\n".join([
                    "[b orange1]MARKET SUMMARY[/b orange1]",
                    "",
                    *summary_lines,
                    "",
                    f"Updated: {datetime.now().strftime('%H:%M:%S')}",
                    "",
                    "[orange1]Controls[/orange1]",
                    "Q = Quit",
                ])
            )

            await asyncio.sleep(REFRESH_RATE)


if __name__ == "__main__":
    BloombergTerminal().run()
