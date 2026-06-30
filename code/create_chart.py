#!/usr/bin/env python3
"""
Stock Candlestick & Volume Advanced Chart Generator

This script reads historical stock data from a CSV file
and generates an interactive advanced charting web page (HTML)
using Plotly, styled to mimic modern financial charting platforms.
"""

import os
import sys
import argparse
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def generate_chart(csv_path: str, output_path: str, ticker: str = None, company_name: str = None):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at '{csv_path}'. Run the scraper first.")
        sys.exit(1)
        
    # Infer ticker if not provided
    if not ticker:
        ticker = os.path.basename(csv_path).split('_')[0].upper()
        
    print(f"Loading stock data from {csv_path} for {ticker}...")
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate Simple Moving Averages (SMAs)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    print(f"Creating advanced interactive chart for {ticker}...")
    # Create subplots with shared x-axis
    # Row 1 (Price/Candlestick): 80% height, Row 2 (Volume): 20% height
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.015,  # Tighter spacing for cohesive charting feel
        row_width=[0.2, 0.8]
    )
    
    # 1. Candlestick Trace (Row 1)
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=ticker,
            increasing_line_color='#089981',  # Bright TradingView green
            decreasing_line_color='#f23645',  # Bright TradingView red
            increasing_fillcolor='#089981',
            decreasing_fillcolor='#f23645',
            hoverlabel=dict(bgcolor='#1e222d'),
            customdata=df['Volume'],
            hovertemplate=(
                f"<b>{ticker}</b><br>"
                "Date: %{{x|%Y-%m-%d}}<br>"
                "Open: $%{{open:.2f}}<br>"
                "High: $%{{high:.2f}}<br>"
                "Low: $%{{low:.2f}}<br>"
                "Close: $%{{close:.2f}}<br>"
                "<extra></extra>"
            )
        ),
        row=1, col=1
    )
    
    # 2. SMA 20 Trace (Row 1 Overlay)
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['SMA20'],
            name='SMA 20',
            line=dict(color='#ff9800', width=1.2),
            hoverinfo='skip',
            mode='lines'
        ),
        row=1, col=1
    )
    
    # 3. SMA 50 Trace (Row 1 Overlay)
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['SMA50'],
            name='SMA 50',
            line=dict(color='#2196f3', width=1.2),
            hoverinfo='skip',
            mode='lines'
        ),
        row=1, col=1
    )
    
    # 4. Volume Trace (Row 2)
    volume_colors = [
        '#089981' if close >= open_val else '#f23645'
        for open_val, close in zip(df['Open'], df['Close'])
    ]
    fig.add_trace(
        go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=volume_colors,
            opacity=0.8,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
            hoverlabel=dict(bgcolor='#1e222d')
        ),
        row=2, col=1
    )
    
    # Format Title Text
    title_text = f"{company_name} ({ticker}) Historical Advanced Chart" if company_name else f"{ticker} Historical Advanced Chart"
    
    # Advanced Layout Configuration (Nasdaq / TradingView dark theme styling)
    fig.update_layout(
        title={
            'text': title_text,
            'y': 0.96,
            'x': 0.02,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'size': 20, 'color': '#ffffff', 'family': 'Inter, sans-serif'}
        },
        template='plotly_dark',
        height=850,
        margin=dict(l=20, r=70, t=80, b=40),  # extra margin on the right for y-axis labels
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            orientation="h",
            bgcolor="rgba(19, 23, 34, 0.8)",
            bordercolor="#2a2e39",
            borderwidth=1,
            font=dict(size=11, color='#d1d4dc')
        ),
        paper_bgcolor='#131722',  # Modern dark theme charcoal background
        plot_bgcolor='#131722',
        hovermode='x',
        dragmode='pan'  # Pan mode by default matches TradingView drag feel
    )
    
    # Configure grid lines, spikes (crosshair), and side placements
    # Side='right' is standard for TradingView-style financial charts
    grid_style = dict(
        gridcolor='#202430',
        zerolinecolor='#202430',
        showspikes=True,
        spikesnap='cursor',
        spikemode='across',
        spikethickness=0.8,
        spikecolor='#858585',
        spikedash='dash',
        side='right'
    )
    
    # Upper Plot (Price) Y-Axis
    fig.update_yaxes(
        title_text="Price (USD)",
        tickprefix="$",
        tickformat=".2f",
        row=1, col=1,
        **grid_style
    )
    
    # Lower Plot (Volume) Y-Axis
    fig.update_yaxes(
        title_text="Volume",
        tickformat=".2s",  # Clean notation like 20M, 5M
        row=2, col=1,
        **grid_style
    )
    
    # X-Axis Styling and Range Selector Buttons
    # Adding the range selector on the upper plot makes it appear cleanly above the chart
    fig.update_xaxes(
        gridcolor='#202430',
        zerolinecolor='#202430',
        showspikes=True,
        spikesnap='cursor',
        spikemode='across',
        spikethickness=0.8,
        spikecolor='#858585',
        spikedash='dash',
        rangeslider=dict(
            visible=True,
            thickness=0.04,
            bgcolor='#1c2030'
        ),
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1W", step="day", stepmode="backward"),
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(step="all", label="MAX")
            ]),
            bgcolor='#1e222d',
            activecolor='#2962ff',
            font=dict(color='#d1d4dc', size=11),
            x=0.98,            # Position range selector on the far right
            xanchor='right',   # Right-align the range selector buttons
            y=1.04             # Placed at the same height above the price plot
        ),
        row=2, col=1
    )
    
    # Ensure folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as self-contained HTML page using CDN for lighter file weight
    fig.write_html(
        output_path,
        include_plotlyjs='cdn',
        config=dict(
            scrollZoom=True,
            displaylogo=False,
            modeBarButtonsToRemove=['select2d', 'lasso2d', 'resetScale2d']
        )
    )
    print(f"Success! Generated advanced chart HTML file at: {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create interactive candlestick chart for stock data.")
    parser.add_argument(
        '-i', '--input-csv',
        type=str,
        default='downloads/AAPL_historical.csv',
        help="Path to the input historical CSV file (default: downloads/AAPL_historical.csv)"
    )
    parser.add_argument(
        '-o', '--output-html',
        type=str,
        default='plots/AAPL_chart.html',
        help="Path to save the output HTML chart (default: plots/AAPL_chart.html)"
    )
    parser.add_argument(
        '-t', '--ticker',
        type=str,
        default=None,
        help="Stock ticker symbol (default: inferred from filename)"
    )
    parser.add_argument(
        '-n', '--company-name',
        type=str,
        default=None,
        help="Company name (default: None)"
    )
    
    args = parser.parse_args()
    generate_chart(args.input_csv, args.output_html, args.ticker, args.company_name)
