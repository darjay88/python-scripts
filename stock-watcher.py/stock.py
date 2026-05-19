#!/usr/bin/env python3

import time
import os
import requests
from collections import deque

TICKER = "AAPL"
MAX_POINTS = 40  # width of graph

prices = deque(maxlen=MAX_POINTS)


def get_price(ticker):
    url = f"=https://finance.yahoo.com/quote/symbols={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()

    data = r.json()
    result = data["quoteResponse"]["result"]

    if not result:
        raise Exception("No data returned")

    return result[0]["regularMarketPrice"]


# Simple ASCII sparkline blocks (low → high)
spark_chars = "▁▂▃▄▅▆▇█"


def render_sparkline(values):
    if not values:
        return ""

    min_v = min(values)
    max_v = max(values)

    if min_v == max_v:
        return "▇" * len(values)

    scale = len(spark_chars) - 1
    line = ""

    for v in values:
        idx = int((v - min_v) / (max_v - min_v) * scale)
        line += spark_chars[idx]

    return line


def clear():
    os.system("clear")


while True:
    try:
        price = get_price(TICKER)
        prices.append(price)

        clear()

        print(f"📈 {TICKER} Live Tracker (updates every 2s)")
        print("-" * 60)

        print(f"Current Price: ${price:.2f}")
        print(f"High (window): ${max(prices):.2f}")
        print(f"Low  (window): ${min(prices):.2f}")

        print("\nPrice History:")
        print(render_sparkline(prices))

        print("\n" + "-" * 60)

        time.sleep(2)

    except KeyboardInterrupt:
        print("\nExiting...")
        break

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
