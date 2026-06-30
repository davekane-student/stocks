#!/usr/bin/env python3
"""
Bulk Stock Processor

This script automates the retrieval, cleaning, and charting of the top 500
NASDAQ stocks by market capitalization, updates the Quarto dropdown, and
prepares the website build.
"""

import os
import sys
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from nasdaq_scraper import NasdaqScraper, adjust_to_weekday
from create_chart import generate_chart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Output directories
DOWNLOADS_DIR = 'downloads'
PLOTS_DIR = 'plots'
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)


def get_top_nasdaq_tickers(limit: int = 500) -> list:
    """Fetches the largest NASDAQ tickers sorted by market capitalization."""
    url = "https://api.nasdaq.com/api/screener/stocks"
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.nasdaq.com",
        "referer": "https://www.nasdaq.com/"
    }
    params = {
        "tableonly": "true",
        "limit": "1000",  # Fetch more to allow filtering and clean sorting
        "exchange": "NASDAQ"
    }
    
    logger.info("Fetching stock list from Nasdaq Stock Screener...")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        rows = data['data']['table']['rows']
        
        df = pd.DataFrame(rows)
        # Convert marketCap to numeric
        df['marketCap_clean'] = df['marketCap'].astype(str).str.replace(',', '', regex=False)
        df['marketCap_clean'] = pd.to_numeric(df['marketCap_clean'], errors='coerce').fillna(0)
        
        # Sort and clean symbols
        df = df.sort_values(by='marketCap_clean', ascending=False)
        
        # Filter to standard symbols (no warrants, preferred, or test tickers)
        # Nasdaq test/special tickers often contain characters like '^', 'w', etc.
        df = df[df['symbol'].str.match(r'^[A-Z\-]+$')]
        
        # Select top N unique tickers
        tickers_info = []
        seen = set()
        for _, row in df.iterrows():
            sym = row['symbol'].strip()
            name = row['name'].strip()
            if sym not in seen and len(sym) <= 5: # standard symbols are 1-5 chars
                seen.add(sym)
                tickers_info.append({'symbol': sym, 'name': name})
                if len(tickers_info) == limit:
                    break
                    
        logger.info(f"Identified the top {len(tickers_info)} NASDAQ companies.")
        return tickers_info
        
    except Exception as e:
        logger.error(f"Error fetching tickers list: {e}")
        sys.exit(1)


def process_single_ticker(ticker_info: dict, from_date: str, to_date: str) -> dict:
    """Downloads historical data and generates the chart for a single ticker."""
    symbol = ticker_info['symbol']
    name = ticker_info['name']
    
    csv_path = os.path.join(DOWNLOADS_DIR, f"{symbol}_historical.csv")
    chart_path = os.path.join(PLOTS_DIR, f"{symbol}_chart.html")
    
    # 1. Download/Retrieve Data
    downloaded = False
    if os.path.exists(csv_path):
        # Already downloaded
        downloaded = True
    else:
        scraper = NasdaqScraper()
        df = scraper.scrape_ticker(symbol, from_date, to_date)
        if df is not None:
            df.to_csv(csv_path, index=False)
            downloaded = True
            # Friendly delay between network requests to avoid Akamai bans
            time.sleep(0.5)
            
    # 2. Generate Chart
    charted = False
    if downloaded:
        try:
            generate_chart(csv_path, chart_path, symbol, name)
            charted = True
        except Exception as e:
            logger.error(f"Failed to generate chart for {symbol}: {e}")
            
    return {
        'symbol': symbol,
        'name': name,
        'downloaded': downloaded,
        'charted': charted
    }


def update_charts_qmd(results: list):
    """Regenerates the charts.qmd page dynamically with the list of successful stock charts."""
    # Filter to only successfully charted stocks
    success_stocks = [r for r in results if r['charted']]
    # Sort alphabetically by symbol
    success_stocks = sorted(success_stocks, key=lambda x: x['symbol'])
    
    logger.info(f"Updating charts.qmd dropdown with {len(success_stocks)} options...")
    
    options_html = []
    for s in success_stocks:
        clean_name = s['name'].replace('"', '&quot;').replace("'", "&apos;")
        options_html.append(f'    <option value="plots/{s["symbol"]}_chart.html">{s["symbol"]} ({clean_name})</option>')
        
    options_str = "\n".join(options_html)
    
    qmd_content = f"""---
title: "Interactive Stock Charts"
---

Choose a stock from the dropdown menu below to load its interactive, dark-mode technical analysis chart. Each chart contains synchronized price (candlestick) and volume panels, moving averages (SMA 20/50), and dynamic range selectors.

<div style="margin-bottom: 25px; display: flex; align-items: center; gap: 10px;">
  <label for="stock-select" style="font-weight: 600; color: #ffffff; font-size: 15px;">Select Ticker:</label>
  <select id="stock-select" onchange="changeStockChart(this.value)" style="background-color: #1e222d; color: #d1d4dc; border: 1px solid #2a2e39; border-radius: 6px; padding: 8px 16px; font-size: 14px; cursor: pointer; outline: none; width: 100%; max-width: 450px;">
{options_str}
  </select>
</div>

::: {{.column-page}}
<iframe id="stock-chart-iframe" src="plots/{success_stocks[0]['symbol']}_chart.html" width="100%" height="900px" style="border: none; background: #131722; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.35);"></iframe>
:::

<script>
function changeStockChart(chartPath) {{
  var iframe = document.getElementById('stock-chart-iframe');
  if (iframe) {{
    iframe.src = chartPath;
  }}
}}
</script>

### Chart Interaction Guide

1. **Date Range Buttons:** Click the buttons in the top-left corner of the chart (`1W`, `1M`, `YTD`, `1Y`, `5Y`, `MAX`) to quickly zoom into specific time horizons.
2. **Interactive Zooming:** Use your mouse scroll-wheel (or pinch-to-zoom on trackpads) over any area of the chart to zoom in or out dynamically.
3. **Panning:** Click and drag the price pane to slide the chart chronologically. The price and volume plots will remain perfectly synchronized.
4. **Moving Average Toggles:** Click the **SMA 20** or **SMA 50** label in the legend to toggle the visibility of the corresponding Simple Moving Average lines.
5. **Crosshair Spikes:** Hover your cursor over the chart to display crosshair gridlines that trace price values on the right-hand Y-axis.
"""
    
    with open('charts.qmd', 'w') as f:
        f.write(qmd_content)
        
    logger.info("Successfully updated charts.qmd.")


def main():
    # Calculate date range (10 years)
    to_date_dt = adjust_to_weekday(datetime.today())
    from_date_dt = adjust_to_weekday(to_date_dt - timedelta(days=10*365))
    
    from_date_str = from_date_dt.strftime('%Y-%m-%d')
    to_date_str = to_date_dt.strftime('%Y-%m-%d')
    
    # Get top 500 NASDAQ tickers
    tickers_info = get_top_nasdaq_tickers(500)
    
    # Run concurrent downloads & charting
    logger.info("Starting bulk data processing and charting...")
    results = []
    
    # We use 6 threads to keep load moderate on Nasdaq endpoints
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_ticker = {
            executor.submit(process_single_ticker, ticker, from_date_str, to_date_str): ticker
            for ticker in tickers_info
        }
        
        completed_count = 0
        for future in as_completed(future_to_ticker):
            completed_count += 1
            res = future.result()
            results.append(res)
            
            if completed_count % 10 == 0 or completed_count == len(tickers_info):
                logger.info(f"Processed {completed_count}/{len(tickers_info)} tickers...")
                
    success_downloads = sum(1 for r in results if r['downloaded'])
    success_charts = sum(1 for r in results if r['charted'])
    logger.info(f"Bulk run completed. Downloads: {success_downloads}/500. Charts: {success_charts}/500.")
    
    # Update Quarto charts qmd
    if success_charts > 0:
        update_charts_qmd(results)
    else:
        logger.error("No charts were generated. Aborting Quarto update.")


if __name__ == '__main__':
    main()
