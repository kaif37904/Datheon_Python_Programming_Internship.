"""Investment Portfolio Tracker (Console)

Run with:  python portfolio.py

- Enter stock ticker, buy price and share quantity for each holding.
- Current prices are looked up from a CSV dataset (e.g. the downloaded
  S&P 500 ticker dataset) if one is placed next to this script as
  'sp500_tickers.csv' or 'prices.csv'. The CSV needs a ticker column
  (Symbol / Ticker) and a price column (Price / Close / Current Price).
- If no CSV is found, a small built-in sample price table is used.
- If a ticker is in neither, you are asked to type the current price.
- Results are printed as a table and written to 'portfolio_summary.csv'.
"""

import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUMMARY_FILE = os.path.join(BASE_DIR, "portfolio_summary.csv")
PRICE_FILES = ["sp500_tickers.csv", "prices.csv"]

TICKER_COLUMNS = ("symbol", "ticker")
PRICE_COLUMNS = ("price", "current price", "close", "last", "last price")

# Sample prices used when no CSV dataset is available
SAMPLE_PRICES = {
    "AAPL": 190.50, "MSFT": 410.20, "GOOGL": 150.75, "AMZN": 175.30,
    "TSLA": 245.10, "META": 480.60, "NVDA": 880.40, "NFLX": 610.90,
    "JPM": 195.25, "KO": 60.15, "DIS": 112.80, "INTC": 42.35,
}


def load_prices():
    """Return {ticker: price}. Reads a CSV if present, otherwise sample data."""
    for name in PRICE_FILES:
        path = os.path.join(BASE_DIR, name)
        if not os.path.exists(path):
            continue
        prices = {}
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue
            cols = {c.strip().lower(): c for c in reader.fieldnames}
            t_col = next((cols[c] for c in TICKER_COLUMNS if c in cols), None)
            p_col = next((cols[c] for c in PRICE_COLUMNS if c in cols), None)
            if not t_col or not p_col:
                continue
            for row in reader:
                try:
                    prices[row[t_col].strip().upper()] = float(row[p_col])
                except (ValueError, AttributeError, TypeError):
                    continue
        if prices:
            print(f"Loaded {len(prices)} prices from {name}")
            return prices
    print("No price CSV found - using built-in sample prices.")
    return dict(SAMPLE_PRICES)


def read_float(prompt, minimum=0.0):
    """Keep asking until the user enters a number greater than minimum."""
    while True:
        text = input(prompt).strip().replace(",", "")
        try:
            value = float(text)
        except ValueError:
            print("  Please enter a valid number.")
            continue
        if value <= minimum:
            print(f"  Value must be greater than {minimum:g}.")
            continue
        return value


def add_position(portfolio, prices):
    ticker = input("Ticker symbol (e.g. AAPL): ").strip().upper()
    if not ticker.isalpha() and not ticker.replace(".", "").replace("-", "").isalnum():
        print("  Invalid ticker.")
        return
    buy_price = read_float("Buy price per share: ")
    shares = read_float("Number of shares: ")

    if ticker in prices:
        current = prices[ticker]
        print(f"  Current price found: {current:.2f}")
    else:
        print(f"  '{ticker}' not found in the price data.")
        current = read_float("  Enter current price manually: ")

    if ticker in portfolio:
        # Merge with an existing holding using weighted average buy price
        old = portfolio[ticker]
        total_shares = old["shares"] + shares
        avg = (old["buy_price"] * old["shares"] + buy_price * shares) / total_shares
        portfolio[ticker] = {"buy_price": avg, "shares": total_shares, "current": current}
        print(f"  Updated {ticker}: {total_shares:g} shares @ avg {avg:.2f}")
    else:
        portfolio[ticker] = {"buy_price": buy_price, "shares": shares, "current": current}
        print(f"  Added {ticker}.")


def calculate(portfolio):
    """Return (rows, total_invested, total_value)."""
    rows = []
    total_invested = total_value = 0.0
    for ticker, p in portfolio.items():
        invested = p["buy_price"] * p["shares"]
        value = p["current"] * p["shares"]
        gain = value - invested
        pct = gain / invested * 100
        rows.append({
            "ticker": ticker, "shares": p["shares"], "buy_price": p["buy_price"],
            "current_price": p["current"], "invested": invested,
            "market_value": value, "gain_loss": gain, "gain_loss_pct": pct,
        })
        total_invested += invested
        total_value += value
    return rows, total_invested, total_value


def print_report(rows, total_invested, total_value):
    header = (f"{'Ticker':<8}{'Shares':>9}{'Buy':>11}{'Current':>11}"
              f"{'Invested':>13}{'Value':>13}{'Gain/Loss':>13}{'%':>9}")
    line = "=" * len(header)
    print("\n" + line)
    print("PORTFOLIO SUMMARY".center(len(header)))
    print(line)
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['ticker']:<8}{r['shares']:>9g}{r['buy_price']:>11.2f}"
              f"{r['current_price']:>11.2f}{r['invested']:>13,.2f}"
              f"{r['market_value']:>13,.2f}{r['gain_loss']:>+13,.2f}"
              f"{r['gain_loss_pct']:>+8.2f}%")
    print("-" * len(header))
    total_gain = total_value - total_invested
    total_pct = total_gain / total_invested * 100 if total_invested else 0.0
    print(f"{'TOTAL':<8}{'':>9}{'':>11}{'':>11}{total_invested:>13,.2f}"
          f"{total_value:>13,.2f}{total_gain:>+13,.2f}{total_pct:>+8.2f}%")
    print(line)
    print("Result:", "PROFIT" if total_gain > 0 else "LOSS" if total_gain < 0 else "BREAK-EVEN")


def save_summary(rows, total_invested, total_value, filename=SUMMARY_FILE):
    fields = ["ticker", "shares", "buy_price", "current_price", "invested",
              "market_value", "gain_loss", "gain_loss_pct"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (round(v, 2) if isinstance(v, float) else v)
                             for k, v in r.items()})
        total_gain = total_value - total_invested
        total_pct = total_gain / total_invested * 100 if total_invested else 0.0
        writer.writerow({
            "ticker": "TOTAL", "invested": round(total_invested, 2),
            "market_value": round(total_value, 2),
            "gain_loss": round(total_gain, 2), "gain_loss_pct": round(total_pct, 2),
        })
    print(f"\nSummary saved to: {filename}")


def main():
    prices = load_prices()
    portfolio = {}
    print("\n=== Investment Portfolio Tracker ===")
    while True:
        print("\n1. Add a holding\n2. View summary and save to CSV\n3. Quit")
        choice = input("Choose an option (1-3): ").strip()
        if choice == "1":
            add_position(portfolio, prices)
        elif choice == "2":
            if not portfolio:
                print("Portfolio is empty. Add a holding first.")
                continue
            rows, invested, value = calculate(portfolio)
            print_report(rows, invested, value)
            save_summary(rows, invested, value)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Enter 1, 2 or 3.")


if __name__ == "__main__":
    main()
