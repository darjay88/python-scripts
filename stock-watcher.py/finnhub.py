#!/usr/bin/env python3

import sys
import requests

API_KEY = "d834sb1r01ql4onganfgd834sb1r01ql4ongang0"

def get_price(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    data = r.json()

    return data["c"]  # current price

def main():
    if len(sys.argv) < 2:
        print("Usage: stock <TICKER>")
        return

    ticker = sys.argv[1].upper()

    try:
        price = get_price(ticker)
        print(f"{ticker}: ${price:.2f}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
