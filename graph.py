from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import io

router = APIRouter()

@router.get("/chart", response_class=HTMLResponse)
def get_ticker_chart(
    ticker: str = Query(..., example="BTC-USD"),
    start: str = Query(..., example="2023-01-01"),
    end: str = Query(..., example="2024-01-01")
):
    # Validate date format
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Fetch data
    data = yf.download(ticker, start=start, end=end)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}' between {start} and {end}")

    # Add SMAs
    data['20_SMA'] = data['Close'].rolling(window=20).mean()
    data['50_SMA'] = data['Close'].rolling(window=50).mean()

    # Build Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Candlestick"
    ))

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name="Close Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data['20_SMA'], mode='lines', name="20-day SMA", line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['50_SMA'], mode='lines', name="50-day SMA", line=dict(dash='dot')))
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', yaxis='y2', marker=dict(color='rgba(0,0,255,0.2)')))

    fig.update_layout(
        title=f"{ticker} Chart ({start} to {end})",
        xaxis_title="Date",
        yaxis=dict(title="Price (USD)"),
        yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False),
        xaxis_rangeslider_visible=True,
        height=700,
        template="plotly_white"
    )

    # Render chart to HTML string
    html_str = fig.to_html(include_plotlyjs='cdn', full_html=False)
    return HTMLResponse(content=html_str)