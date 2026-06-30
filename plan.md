# Plan of Action: Nasdaq Stock Historical Price Data Scraper

This plan outlines the design and implementation steps for building a robust Python-based dataset collector that gathers historical stock price data from the [Nasdaq Historical Quotes page](https://www.nasdaq.com/market-activity/quotes/historical).

---

## 1. Technical Analysis

### A. Target API Endpoint
The Nasdaq website dynamically retrieves stock data using JavaScript from an internal JSON API. Programmatic requests directly to the web pages are slow and heavily filtered, but targeting the internal API endpoint is faster and cleaner:
* **Endpoint URL:** `https://api.nasdaq.com/api/quote/{symbol}/historical`
* **Query Parameters:**
  * `assetclass`: Set to `stocks` (or `etf`, etc.)
  * `fromdate`: Start date (e.g., `YYYY-MM-DD`, such as `2025-06-30`)
  * `todate`: End date (e.g., `YYYY-MM-DD`, such as `2026-06-30`)
  * `limit`: The maximum number of records to retrieve. Setting this to a high value (like `9999`) allows fetching the full requested range in a single request.

### B. Anti-Scraping & Request Headers
Nasdaq uses security layers (like Akamai) that block requests lacking appropriate browser headers. To bypass basic filters, we must supply realistic headers:
* `User-Agent`: A modern browser user agent (e.g., Chrome/Firefox)
* `Accept`: `application/json, text/plain, */*`
* `Accept-Language`: `en-US,en;q=0.9`
* `Origin`: `https://www.nasdaq.com`
* `Referer`: `https://www.nasdaq.com/`

---

## 2. Implementation Status

### [Completed] Phase 1: Verification (Proof of Concept)
1. Created and ran verification scripts (`verify_nasdaq.py` and `test_nasdaq_depth.py`) under scratch.
2. Determined that requesting weekend dates directly triggers Nasdaq API Error 1000 ("Something went wrong"). Added weekday adjustments to circumvent this limit.

### [Completed] Phase 2: Data Cleaning & Standardizing
Implemented formatting conversions for:
* **Date:** `MM/DD/YYYY` $\rightarrow$ `YYYY-MM-DD`
* **Close/Last, Open, High, Low:** Strings like `$182.50` $\rightarrow$ Floats like `182.50`
* **Volume:** Strings like `52,345,123` $\rightarrow$ Integers like `52345123`

### [Completed] Phase 3: Building the Robust Scraper Class
Created [nasdaq_scraper.py](file:///workspaces/stocks/code/nasdaq_scraper.py):
* Handled weekday date-shifting for weekend safety.
* Added standard connection error handling and timeouts.
* Formatted logs via python `logging`.

### [Completed] Phase 4: Data Storage & CLI
* Created [downloads/AAPL_historical.csv](file:///workspaces/stocks/downloads/AAPL_historical.csv) containing 2510 rows (10 years) of clean trading records.
* Expanded the dataset by scraping the 500 largest NASDAQ tickers by market cap.
* Supported configurable outputs via parameters.

### [Completed] Phase 5: Documentation & Verification
* Created [README.md](file:///workspaces/stocks/README.md) file detailing how to install requirements and execute the scraper for other symbols.

### [Completed] Phase 6: Interactive Advanced Charting
* Developed [create_chart.py](file:///workspaces/stocks/code/create_chart.py) using Plotly.
* Configured subplots syncing candlestick data (OHLC) and transaction volumes.
* Generated interactive HTML charts for all 500 NASDAQ stocks inside [plots/](file:///workspaces/stocks/plots/).
* Re-designed the Quarto dashboard [charts.qmd](file:///workspaces/stocks/charts.qmd) to include a dynamic HTML/JS dropdown selector for all 500 stocks.
