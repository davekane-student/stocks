#!/usr/bin/env python3
"""
Nasdaq Historical Quotes Scraper

This script fetches historical stock price data directly from Nasdaq's
internal API and exports it as a cleaned CSV dataset.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.nasdaq.com',
    'referer': 'https://www.nasdaq.com/'
}
API_URL_TEMPLATE = 'https://api.nasdaq.com/api/quote/{symbol}/historical'


class NasdaqScraper:
    """A scraper class to retrieve and clean historical stock data from Nasdaq's API."""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_raw_data(self, symbol: str, from_date: str, to_date: str, limit: int = 9999) -> Optional[Dict[str, Any]]:
        """
        Fetches historical data for a symbol from Nasdaq API.
        
        Args:
            symbol: Ticker symbol (e.g., AAPL).
            from_date: Start date string in YYYY-MM-DD format.
            to_date: End date string in YYYY-MM-DD format.
            limit: Maximum number of rows to retrieve.
            
        Returns:
            The raw JSON dictionary returned by Nasdaq API, or None if error occurs.
        """
        url = API_URL_TEMPLATE.format(symbol=symbol.upper())
        params = {
            'assetclass': 'stocks',
            'fromdate': from_date,
            'todate': to_date,
            'limit': str(limit)
        }
        
        logger.info(f"Fetching {symbol.upper()} historical quotes from {from_date} to {to_date}...")
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            
            # Handle rate limiting / server errors
            if response.status_code == 429:
                logger.warning("Rate limited (429). Waiting 5 seconds before returning None...")
                time.sleep(5)
                return None
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error for ticker {symbol}: {e}")
            return None

    def clean_data(self, raw_json: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Cleans and parses the raw JSON data into a pandas DataFrame.
        
        Args:
            raw_json: Raw JSON dictionary from the Nasdaq API.
            
        Returns:
            A cleaned pandas DataFrame or None if parsing fails.
        """
        try:
            data_sec = raw_json.get('data')
            if not data_sec:
                logger.error("No 'data' section found in the Nasdaq response.")
                return None
                
            trades_table = data_sec.get('tradesTable')
            if not trades_table or 'rows' not in trades_table:
                logger.error("No tradesTable or rows found in Nasdaq response.")
                return None
                
            rows = trades_table['rows']
            if not rows:
                logger.warning("The API returned an empty list of rows for this date range.")
                return None
                
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Expected columns: ['date', 'close', 'volume', 'open', 'high', 'low']
            # We want to convert column names to a standard format and clean their values
            df = df.rename(columns={
                'date': 'Date',
                'close': 'Close',
                'volume': 'Volume',
                'open': 'Open',
                'high': 'High',
                'low': 'Low'
            })
            
            # Clean prices (remove '$' and convert to float)
            price_cols = ['Close', 'Open', 'High', 'Low']
            for col in price_cols:
                if col in df.columns:
                    # Strip spaces, '$' and commas
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                    df[col] = df[col].str.replace(',', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Clean volume (remove commas and convert to integer)
            if 'Volume' in df.columns:
                df['Volume'] = df['Volume'].astype(str).str.replace(',', '', regex=False)
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype('int64')
                
            # Convert date to standard YYYY-MM-DD
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
                # Drop rows with invalid dates
                df = df.dropna(subset=['Date'])
                
            # Sort chronologically (oldest to newest)
            df = df.sort_values(by='Date').reset_index(drop=True)
            
            # Format Date column back to YYYY-MM-DD string
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # Ensure correct columns and order
            final_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in final_cols if col in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"Error occurred while cleaning the data: {e}")
            return None

    def scrape_ticker(self, symbol: str, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
        """
        High-level method to fetch and clean data for a single symbol.
        """
        raw_data = self.fetch_raw_data(symbol, from_date, to_date)
        if not raw_data:
            return None
        return self.clean_data(raw_data)


def adjust_to_weekday(dt: datetime) -> datetime:
    """Adjusts a datetime object to the nearest previous weekday if it falls on a weekend."""
    wd = dt.weekday()  # 0=Monday, 5=Saturday, 6=Sunday
    if wd == 5:  # Saturday
        return dt - timedelta(days=1)
    elif wd == 6:  # Sunday
        return dt - timedelta(days=2)
    return dt


def main():
    parser = argparse.ArgumentParser(description="Scrape Nasdaq historical stock quotes.")
    parser.add_argument(
        '-t', '--ticker', 
        type=str, 
        default='AAPL', 
        help="Stock ticker symbol to scrape (default: AAPL)"
    )
    parser.add_argument(
        '-f', '--from-date', 
        type=str, 
        default=None, 
        help="Start date in YYYY-MM-DD format (default: 10 years ago)"
    )
    parser.add_argument(
        '-u', '--to-date', 
        type=str, 
        default=None, 
        help="End date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        '-o', '--output-dir', 
        type=str, 
        default='downloads', 
        help="Directory to save downloaded CSV files (default: downloads)"
    )
    
    args = parser.parse_args()
    
    # Calculate default dates if not provided
    to_date_dt = datetime.today()
    if args.to_date:
        try:
            to_date_dt = datetime.strptime(args.to_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid to-date format: {args.to_date}. Must be YYYY-MM-DD.")
            sys.exit(1)
            
    to_date_dt = adjust_to_weekday(to_date_dt)
            
    from_date_dt = to_date_dt - timedelta(days=10*365)  # 10 years ago default
    if args.from_date:
        try:
            from_date_dt = datetime.strptime(args.from_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid from-date format: {args.from_date}. Must be YYYY-MM-DD.")
            sys.exit(1)
            
    from_date_dt = adjust_to_weekday(from_date_dt)
            
    from_date_str = from_date_dt.strftime('%Y-%m-%d')
    to_date_str = to_date_dt.strftime('%Y-%m-%d')
    
    # Ensure directories exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize scraper
    scraper = NasdaqScraper()
    df = scraper.scrape_ticker(args.ticker, from_date_str, to_date_str)
    
    if df is not None:
        output_file = os.path.join(args.output_dir, f"{args.ticker.upper()}_historical.csv")
        df.to_csv(output_file, index=False)
        logger.info(f"Successfully saved {len(df)} rows of data for {args.ticker.upper()} to '{output_file}'")
    else:
        logger.error(f"Failed to retrieve data for {args.ticker.upper()}")
        sys.exit(1)


if __name__ == '__main__':
    main()
