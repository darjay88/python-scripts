from textual.app import App, ComposeResult
from textual.widgets import DataTable
from textual.reactive import reactive
from textual import work

import requests
import asyncio

API_KEY = "d834sb1r01ql4onganfgd834sb1r01ql4ongang0"
TICKERS = ["AAPL", "TSLA", "NVDA", "AMD"]


def fetch_quote(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    data = r.json()

    return {
        "price": data["c"],
        "prev": data["pc"],
    }


def format_change(price, prev):
    diff = price - prev
    pct = (diff / prev) * 100 if prev else 0
    return diff, pct


class StockApp(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        self.table = DataTable()
        yield self.table

    def on_mount(self):
        self.table.add_columns("Ticker", "Price", "Change", "%")
        self.load_data()

    @work
    async def load_data(self):
        while True:
            self.table.clear()

            for t in TICKERS:
                try:
                    data = fetch_quote(t)

                    price = data["price"]
                    prev = data["prev"]

                    diff, pct = format_change(price, prev)

                    sign = "↑" if diff > 0 else "↓" if diff < 0 else "→"

                    self.table.add_row(
                        t,
                        f"{price:.2f}",
                        f"{sign} {diff:+.2f}",
                        f"{pct:+.2f}%",
                    )

                except Exception:
                    self.table.add_row(t, "ERR", "", "")

            await asyncio.sleep(2)


if __name__ == "__main__":
    StockApp().run()
