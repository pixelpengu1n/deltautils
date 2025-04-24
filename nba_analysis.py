from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
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

NBA_TEAMS = [
    "Cleveland", "Memphis", "Denver", "Oklahoma City", "Atlanta", "Chicago",
    "Indiana", "Boston", "New York", "Sacramento", "Detroit", "Dallas",
    "Milwaukee", "Phoenix", "Minnesota", "Houston", "San Antonio", "Golden State",
    "LA Lakers", "LA Clippers", "Utah", "Portland", "Toronto", "New Orleans",
    "Miami", "Philadelphia", "Washington", "Charlotte", "Brooklyn", "Orlando"
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_crypto_events_from_yahoo(ticker: str, start: str, end: str, interval: str):
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
        return []


def generate_summary_insight(events, team1, team2, start, end, ticker):
    price_points = [(e["event_time"], e["open"], e["close"], e["volume"]) for e in events if e.get("close") is not None]
    summary_lines = [
        f"{d.strftime('%Y-%m-%d')}: Open=${o:.2f}, Close=${c:.2f}, Volume={int(v)}"
        for d, o, c, v in price_points
    ]
    history = "\n".join(summary_lines)
    prompt = f"""
You are a sports and market analyst AI. Given the following crypto price history for {ticker} and an NBA matchup between {team1} and {team2}, generate an analysis of how {ticker} trends may influence NBA outcomes and fan behavior.

Crypto price history ({len(price_points)} days) between {start} and {end}:
{history}

Use these factors:
- Sponsorships (e.g., Crypto.com Arena, FTX)
- Player endorsements (e.g., NFTs, crypto deals)
- Fan engagement and betting trends (e.g., DraftKings, Coinbase)
- Social media sentiment and media coverage

Assume NBA performance metrics are available. Include plausible interpretations as if analyzing real stats.

Return a detailed multi-paragraph summary with insights and 2–3 links.
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
        return generate_placeholder_plot("No crypto events available")

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


def generate_placeholder_plot(message="No events available"):
    plt.figure(figsize=(8, 2))
    plt.text(0.5, 0.5, message, fontsize=12, ha='center')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@router.get("/impact/nba/analysis")
async def analyze_impact(
    team1: str = "LA Lakers",
    team2: str = "Boston",
    start_date: str = Query(..., description="Start date for crypto data (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date for crypto data (YYYY-MM-DD)"),
    ticker: str = Query("BTC-USD", description="Crypto ticker")
):
    if team1 not in NBA_TEAMS or team2 not in NBA_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid NBA team names.")

    try:
        parse_date(start_date)
        parse_date(end_date)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    events = fetch_crypto_events_from_yahoo(ticker, start_date, end_date, "1d")
    timeline_img = generate_timeline_plot(events)
    summary = generate_summary_insight(events, team1, team2, start_date, end_date, ticker)

    return JSONResponse(content={
        "meta": {
            "ticker": ticker,
            "team1": team1,
            "team2": team2,
            "cryptoStartDate": start_date,
            "cryptoEndDate": end_date,
        },
        "chart": {
            "timelineImageBase64": timeline_img
        },
        "insight": {
            "summary": summary
        }
    })
