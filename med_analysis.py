from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from dateutil.parser import parse as parse_date
import pandas as pd
import yfinance as yf
import os
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Secure usage of API key

def fetch_crypto_events_from_yahoo(ticker: str, start: str, end: str, interval: str = "1d"):
    try:
        data = yf.download(ticker, start=start, end=end, interval=interval)
        if data.empty:
            return []

        data.reset_index(inplace=True)
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        events = []
        for _, row in data.iterrows():
            event = {
                "event_time": datetime.fromisoformat(row["Date"].replace("Z", "+00:00")),
                "event_type": "crypto_price_update",
                "description": f"Price update for {ticker}",
                "open": row.get("Open"),
                "high": row.get("High"),
                "low": row.get("Low"),
                "close": row.get("Close"),
                "volume": row.get("Volume"),
            }
            events.append(event)
        return events
    except Exception as e:
        print(f"Error fetching crypto data: {e}")
        return []

def generate_medical_summary(ticker, events, region, start, end):
    price_points = [(e["event_time"], e["open"], e["close"], e["volume"]) for e in events if e.get("close") is not None]
    history = "\n".join(
        f"{d.strftime('%Y-%m-%d')}: Open=${o:.2f}, Close=${c:.2f}, Volume={int(v)}"
        for d, o, c, v in price_points
    )

    prompt = f"""
You are a global health and economics research AI. Analyze how the following cryptocurrency {ticker} fluctuations from {start} to {end} might have impacted the healthcare domain in {region}.

Crypto price history ({len(price_points)} days):
{history}

Consider:
- Influence on private health startup investments
- Charitable donation trends for disease support during crypto booms
- Mental health effects of volatile crypto trends
- Public health behavior shifts due to financial stress
- Global healthcare budget adaptation amid market changes

Structure your response into 2–3 paragraphs and include 2 suggested references or datasets at the end.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[AI Summary unavailable: {e}]"

def generate_timeline_plot(events):
    dates = [e["event_time"] for e in events]
    types = [e.get("event_type", "Unknown") for e in events]
    if not dates:
        return ""

    plt.figure(figsize=(10, 2))
    plt.hlines(1, min(dates), max(dates), colors="lightgray")
    plt.eventplot(dates, lineoffsets=1, linelengths=0.4, colors="blue")
    for i, d in enumerate(dates):
        plt.text(d, 1.02, types[i], rotation=45, ha='right', fontsize=8)
    plt.title("Crypto Events Timeline")
    plt.yticks([])
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

@router.get("/impact/medical/analysis")
async def analyze_medical_impact(
    region: str = Query("Australia", description="Region or country for health impact focus"),
    start_date: str = Query(..., description="Start date for crypto analysis (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date for crypto analysis (YYYY-MM-DD)"),
    ticker: str = Query("BTC-USD", description="Cryptocurrency ticker"),
):
    try:
        parse_date(start_date)
        parse_date(end_date)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    events = fetch_crypto_events_from_yahoo(ticker, start_date, end_date)
    timeline_img = generate_timeline_plot(events) if events else ""
    summary = generate_medical_summary(ticker, events, region, start_date, end_date)

    return {
        "meta": {
            "region": region,
            "cryptoTicker": ticker,
            "dateRange": f"{start_date} to {end_date}",
        },
        "visualisation": {
            "timelineImageBase64": timeline_img
        },
        "insights": {
            "gptSummary": summary
        }
    }
