# Nasdaq Historical Stock Quotes Dataset Builder

This repository contains a robust, automated pipeline to gather historical stock price data directly from Nasdaq's Historical Quotes API and format it into clean CSV datasets.

## Directory Structure

*   [code/](file:///workspaces/stocks/code/)
    *   [nasdaq_scraper.py](file:///workspaces/stocks/code/nasdaq_scraper.py): The primary Python module and command line interface for downloading and cleaning historical quotes.
    *   [create_chart.py](file:///workspaces/stocks/code/create_chart.py): An advanced charting script that uses Plotly to generate an interactive candlestick and volume plot HTML page.
*   [downloads/](file:///workspaces/stocks/downloads/)
    *   [AAPL_historical.csv](file:///workspaces/stocks/downloads/AAPL_historical.csv): The compiled 10-year historical dataset for Apple Inc. (AAPL) in chronological order.
    *   Other downloaded CSVs: Contains historical datasets for **MSFT**, **GOOGL**, **AMZN**, **NVDA**, **META**, **TSLA**, **AVGO**, **COST**, **NFLX**, and **PEP**.
*   [plots/](file:///workspaces/stocks/plots/)
    *   [AAPL_chart.html](file:///workspaces/stocks/plots/AAPL_chart.html): The interactive dark-mode charting web page for AAPL.

## Requirements

The project uses standard data science libraries. You can install the requirements via:

```bash
pip install requests pandas plotly
```

## Usage

### Download Ticker Data (e.g., AAPL)
```bash
python code/nasdaq_scraper.py --ticker AAPL --output-dir downloads
```

### Download Custom Date Range
```bash
python code/nasdaq_scraper.py --ticker MSFT --from-date 2020-01-01 --to-date 2025-12-31 --output-dir downloads
```

### Generate Advanced Chart Page
```bash
python code/create_chart.py --input-csv downloads/AAPL_historical.csv --output-html plots/AAPL_chart.html
```

Open the generated [AAPL_chart.html](file:///workspaces/stocks/plots/AAPL_chart.html) directly in any browser to interact with the chart!

## Features

1.  **Auto Weekend Date Handling:** The Nasdaq API throws a server error (`code 1000`) if the requested start or end dates fall on weekends. The script automatically detects and shifts weekend dates to the nearest trading day.
2.  **Robust Cleaning Pipeline:** Parses raw API data, strips formatting characters (`$`, commas), handles type conversion, and exports standard columns: `Date`, `Open`, `High`, `Low`, `Close`, and `Volume`.
3.  **Sorted Output:** Chronologically ordered from oldest to newest trading days.
4.  **Advanced Subplot Visualization:** The charting page features interactive candlestick charting synced with daily volume bars and dynamic range selectors (1M, 3M, 6M, YTD, 1Y, 5Y, ALL).

