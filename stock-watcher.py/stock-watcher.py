#!/usr/bin/env python3

import time
import requests
import os

# Change this to any stock ticker you want
TICKER = "SOFI"

def get_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    
    response = requests.get(url)
    data = response.json()

    result = data["chart"]["result"][0]
    price = result["meta"]["regularMarketPrice"]

    return price

while True:
    try:
        price = get_price(TICKER)

        # Clear terminal
        os.system("clear")

        print(f"Stock Tracker")
        print(f"Ticker: {TICKER}")
        print(f"Current Price: ${price}")

        time.sleep(2)

    except KeyboardInterrupt:
        print("\nExiting...")
        break

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
