#!/usr/bin/env python3
"""
Daily Financial Markets Newsletter
===================================
Generates a comprehensive HTML newsletter and sends it via email.

Environment Variables Required:
  NEWSAPI_KEY     - API key from newsapi.org (free tier: 100 req/day)
  EMAIL_ADDRESS   - Your Outlook/Gmail email address (optional)
  EMAIL_PASSWORD  - App password (optional)
  EMAIL_TO        - Recipient email (defaults to EMAIL_ADDRESS)
  SMTP_SERVER     - SMTP server (defaults to smtp-mail.outlook.com)
  SMTP_PORT       - SMTP port (defaults to 587)
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json

# ---------------------
# CONFIGURATION
# ---------------------

# Market indices to track
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI": "DOW 30",
    "^GSPTSE": "TSX (Canada)",
    "^VIX": "VIX (Fear Index)",
    "BTC-USD": "Bitcoin",
    "CL=F": "Crude Oil",
    "GC=F": "Gold",
    "^TNX": "10Y Treasury Yield",
    "DX-Y.NYB": "US Dollar Index",
}

# Your personal watchlist
WATCHLIST = {
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "TSM": "TSMC",
    "ASML": "ASML",
    "AXON": "Axon Enterprise",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "AVGO": "Broadcom",
    "ARM": "ARM Holdings",
    "PLTR": "Palantir",
    "SMCI": "Super Micro",
}

# Broader list for finding top movers
MOVERS_UNIVERSE = [
    "NVDA", "TSLA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "AVGO", "ARM", "PLTR", "SMCI", "TSM", "ASML", "AXON", "CRM",
    "NFLX", "COIN", "MARA", "RIOT", "SOFI", "NU", "SQ", "SHOP",
    "SNOW", "MDB", "NET", "DDOG", "ZS", "CRWD", "PANW", "ABNB",
    "UBER", "LYFT", "RIVN", "LCID", "NIO", "LI", "XPEV", "BABA",
    "JD", "PDD", "SE", "GRAB", "MELI", "DIS", "WMT", "COST",
    "JPM", "GS", "V", "MA", "BRK-B", "UNH", "LLY", "NVO",
    "ORCL", "ADBE", "NOW", "INTU", "MU", "QCOM", "INTC", "TXN",
]

# News search queries for market-moving news
MARKET_NEWS_QUERIES = [
    "stock market OR Wall Street OR S&P 500",
    "Federal Reserve OR interest rates OR inflation",
    "Trump tariff OR trade war OR sanctions",
    "Jensen Huang OR NVIDIA AI",
    "earnings report OR earnings beat OR earnings miss",
    "IPO OR stock split OR buyback",
]

# Sports news query
SPORTS_QUERY = "NHL OR NBA OR NFL OR FIFA OR MLB"

# Global macro query
GLOBAL_MACRO_QUERY = "geopolitics OR oil prices OR China economy OR G7 OR NATO OR Bank of Canada"


# ---------------------
# DATA FETCHING
# ---------------------

def fetch_stock_data(tickers):
    """Fetch current price and daily change for a list of tickers using yfinance."""
    try:
        import yfinance as yf
        data = {}
        # Download all tickers at once for efficiency
        tickers_str = " ".join(tickers)
        raw = yf.download(tickers_str, period="5d", group_by="ticker", progress=False, threads=True)
        
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    hist = raw
                else:
                    hist = raw[ticker] if ticker in raw.columns.get_level_values(0) else None
                
                if hist is not None and len(hist) >= 2:
                    hist = hist.dropna()
                    if len(hist) >= 2:
                        current = float(hist["Close"].iloc[-1])
                        previous = float(hist["Close"].iloc[-2])
                        change = current - previous
                        change_pct = (change / previous) * 100
                        data[ticker] = {
                            "price": current,
                            "change": change,
                            "change_pct": change_pct,
                        }
            except Exception as e:
                print(f"  Warning: Could not process {ticker}: {e}")
                continue
        return data
    except ImportError:
        print("ERROR: yfinance not installed. Run: pip install yfinance")
        return {}
    except Exception as e:
        print(f"ERROR fetching stock data: {e}")
        return {}


def fetch_news(query, category=None, page_size=5):
    """Fetch news articles from NewsAPI."""
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        print("WARNING: NEWSAPI_KEY not set. Skipping news fetch.")
        return []
    
    try:
        import requests
        
        if category:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": api_key,
                "category": category,
                "language": "en",
                "pageSize": page_size,
            }
        else:
            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": api_key,
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "ok":
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published": article.get("publishedAt", ""),
                })
            return articles
        else:
            print(f"  NewsAPI error: {data.get('message', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"  ERROR fetching news for '{query}': {e}")
        return []


def get_fear_greed(vix_value):
    """Calculate Fear & Greed indicator based on VIX levels."""
    if vix_value is None:
        return "N/A", "#888888", "No data"
    
    if vix_value < 12:
        return "Extreme Greed", "#00ff00", "Markets are euphoric — be cautious"
    elif vix_value < 17:
        return "Greed", "#66ff66", "Markets are optimistic — momentum favored"
    elif vix_value < 20:
        return "Neutral", "#ffff00", "Markets are balanced — stock picking matters"
    elif vix_value < 25:
        return "Fear", "#ff6600", "Markets are nervous — watch for dips to buy"
    elif vix_value < 30:
        return "High Fear", "#ff3300", "Markets are stressed — opportunities emerging"
    else:
        return "Extreme Fear", "#ff0000", "Markets are panicking — historically a buying zone"


# ---------------------
# HTML EMAIL BUILDER
# ---------------------

def format_change(change_pct, include_arrow=True):
    """Format a percentage change with color and arrow."""
    if change_pct is None:
        return '<span style="color:#888888;">N/A</span>'
    
    color = "#00ff88" if change_pct >= 0 else "#ff4444"
    arrow = "▲" if change_pct >= 0 else "▼"
    sign = "+" if change_pct >= 0 else ""
    
    if include_arrow:
        return f'<span style="color:{color};font-weight:bold;">{arrow} {sign}{change_pct:.2f}%</span>'
    else:
        return f'<span style="color:{color};font-weight:bold;">{sign}{change_pct:.2f}%</span>'


def format_price(price):
    """Format price with appropriate decimal places."""
    if price is None:
        return "N/A"
    if price > 1000:
        return f"{price:,.0f}"
    elif price > 10:
        return f"{price:,.2f}"
    else:
        return f"{price:,.4f}"


def build_html(indices_data, watchlist_data, movers_data, market_news, global_news, sports_news, vix_value):
    """Build the full HTML email newsletter."""
    
    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    
    # Fear & Greed
    sentiment, sentiment_color, sentiment_note = get_fear_greed(vix_value)
    
    # Find top gainers and losers from movers data
    sorted_movers = sorted(movers_data.items(), key=lambda x: x[1].get("change_pct", 0), reverse=True)
    top_gainers = sorted_movers[:5]
    top_losers = sorted_movers[-5:][::-1]  # Reverse to show worst first
    
    # ---- START HTML ----
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#0a0a0f;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">
<div style="max-width:680px;margin:0 auto;padding:20px;">

<!-- HEADER -->
<div style="text-align:center;padding:30px 20px;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;margin-bottom:20px;">
  <h1 style="margin:0;font-size:28px;color:#00ff88;letter-spacing:1px;">📊 DAILY MARKET BRIEF</h1>
  <p style="margin:8px 0 0;color:#8888aa;font-size:14px;">{date_str}</p>
  <p style="margin:4px 0 0;color:#666688;font-size:12px;">Your personalized financial markets newsletter</p>
</div>

<!-- SENTIMENT GAUGE -->
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;border-left:4px solid {sentiment_color};">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <p style="margin:0;color:#8888aa;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Market Sentiment</p>
      <h2 style="margin:5px 0;color:{sentiment_color};font-size:24px;">{sentiment}</h2>
      <p style="margin:0;color:#8888aa;font-size:13px;">VIX: {format_price(vix_value)} — {sentiment_note}</p>
    </div>
    <div style="font-size:40px;">{"🟢" if vix_value and vix_value < 17 else "🟡" if vix_value and vix_value < 25 else "🔴"}</div>
  </div>
</div>

<!-- MARKET INDICES -->
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;">
  <h3 style="margin:0 0 15px;color:#00ff88;font-size:16px;text-transform:uppercase;letter-spacing:1px;">🏛️ Market Indices & Commodities</h3>
  <table style="width:100%;border-collapse:collapse;">
    <tr style="border-bottom:1px solid #222233;">
      <th style="text-align:left;padding:8px;color:#666688;font-size:12px;">INDEX</th>
      <th style="text-align:right;padding:8px;color:#666688;font-size:12px;">PRICE</th>
      <th style="text-align:right;padding:8px;color:#666688;font-size:12px;">CHANGE</th>
    </tr>"""
    
    # Add index rows
    for ticker, name in INDICES.items():
        d = indices_data.get(ticker, {})
        price = d.get("price")
        change_pct = d.get("change_pct")
        html += f"""
    <tr style="border-bottom:1px solid #1a1a2a;">
      <td style="padding:10px 8px;font-size:14px;"><strong>{name}</strong><br><span style="color:#666688;font-size:11px;">{ticker}</span></td>
      <td style="text-align:right;padding:10px 8px;font-size:14px;font-family:monospace;">{format_price(price)}</td>
      <td style="text-align:right;padding:10px 8px;font-size:14px;">{format_change(change_pct)}</td>
    </tr>"""
    
    html += """
  </table>
</div>

<!-- YOUR WATCHLIST -->
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;">
  <h3 style="margin:0 0 15px;color:#00ff88;font-size:16px;text-transform:uppercase;letter-spacing:1px;">👀 Your Watchlist</h3>
  <table style="width:100%;border-collapse:collapse;">
    <tr style="border-bottom:1px solid #222233;">
      <th style="text-align:left;padding:8px;color:#666688;font-size:12px;">STOCK</th>
      <th style="text-align:right;padding:8px;color:#666688;font-size:12px;">PRICE</th>
      <th style="text-align:right;padding:8px;color:#666688;font-size:12px;">CHANGE</th>
    </tr>"""
    
    # Sort watchlist by change percentage
    watchlist_sorted = sorted(
        WATCHLIST.items(),
        key=lambda x: watchlist_data.get(x[0], {}).get("change_pct", 0),
        reverse=True
    )
    
    for ticker, name in watchlist_sorted:
        d = watchlist_data.get(ticker, {})
        price = d.get("price")
        change_pct = d.get("change_pct")
        html += f"""
    <tr style="border-bottom:1px solid #1a1a2a;">
      <td style="padding:10px 8px;font-size:14px;"><strong>{name}</strong><br><span style="color:#666688;font-size:11px;">{ticker}</span></td>
      <td style="text-align:right;padding:10px 8px;font-size:14px;font-family:monospace;">${format_price(price)}</td>
      <td style="text-align:right;padding:10px 8px;font-size:14px;">{format_change(change_pct)}</td>
    </tr>"""
    
    html += """
  </table>
</div>

<!-- TOP MOVERS -->
<div style="display:flex;gap:15px;margin-bottom:20px;">
  <div style="flex:1;background:#12121a;border-radius:10px;padding:20px;">
    <h3 style="margin:0 0 15px;color:#00ff88;font-size:14px;text-transform:uppercase;">🚀 Top Gainers</h3>"""
    
    for ticker, d in top_gainers:
        html += f"""
    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a1a2a;">
      <span style="font-size:13px;font-weight:bold;">{ticker}</span>
      {format_change(d.get("change_pct"))}
    </div>"""
    
    html += """
  </div>
  <div style="flex:1;background:#12121a;border-radius:10px;padding:20px;">
    <h3 style="margin:0 0 15px;color:#ff4444;font-size:14px;text-transform:uppercase;">📉 Top Losers</h3>"""
    
    for ticker, d in top_losers:
        html += f"""
    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a1a2a;">
      <span style="font-size:13px;font-weight:bold;">{ticker}</span>
      {format_change(d.get("change_pct"))}
    </div>"""
    
    html += """
  </div>
</div>"""
    
    # ---- MARKET NEWS ----
    html += """
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;">
  <h3 style="margin:0 0 15px;color:#00ff88;font-size:16px;text-transform:uppercase;letter-spacing:1px;">📰 Market-Moving News</h3>"""
    
    if market_news:
        for article in market_news[:10]:
            html += f"""
  <div style="padding:12px 0;border-bottom:1px solid #1a1a2a;">
    <a href="{article['url']}" style="color:#4da6ff;text-decoration:none;font-size:14px;font-weight:bold;">{article['title']}</a>
    <p style="margin:5px 0 0;color:#888888;font-size:12px;">{article['source']} • {article.get('published', '')[:10]}</p>
  </div>"""
    else:
        html += '<p style="color:#666688;font-size:13px;">No market news available — check your NEWSAPI_KEY.</p>'
    
    html += "\n</div>"
    
    # ---- GLOBAL MACRO ----
    html += """
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;">
  <h3 style="margin:0 0 15px;color:#00ff88;font-size:16px;text-transform:uppercase;letter-spacing:1px;">🌍 Global Macro & Geopolitics</h3>"""
    
    if global_news:
        for article in global_news[:5]:
            html += f"""
  <div style="padding:12px 0;border-bottom:1px solid #1a1a2a;">
    <a href="{article['url']}" style="color:#4da6ff;text-decoration:none;font-size:14px;font-weight:bold;">{article['title']}</a>
    <p style="margin:5px 0 0;color:#888888;font-size:12px;">{article['source']}</p>
  </div>"""
    else:
        html += '<p style="color:#666688;font-size:13px;">No global macro news available.</p>'
    
    html += "\n</div>"
    
    # ---- SPORTS ----
    html += """
<div style="background:#12121a;border-radius:10px;padding:20px;margin-bottom:20px;">
  <h3 style="margin:0 0 15px;color:#00ff88;font-size:16px;text-transform:uppercase;letter-spacing:1px;">⚽ Sports Headlines</h3>"""
    
    if sports_news:
        for article in sports_news[:5]:
            html += f"""
  <div style="padding:10px 0;border-bottom:1px solid #1a1a2a;">
    <a href="{article['url']}" style="color:#4da6ff;text-decoration:none;font-size:13px;">{article['title']}</a>
    <span style="color:#666688;font-size:11px;"> — {article['source']}</span>
  </div>"""
    else:
        html += '<p style="color:#666688;font-size:13px;">No sports news available.</p>'
    
    html += "\n</div>"
    
    # ---- FOOTER ----
    html += f"""
<div style="text-align:center;padding:20px;color:#444466;font-size:11px;">
  <p>Generated at {now.strftime("%I:%M %p %Z")} • Data from Yahoo Finance & NewsAPI</p>
  <p>⚠️ This is not financial advice. Always do your own research.</p>
  <p style="color:#333344;">Powered by Python & GitHub Actions ⚡</p>
</div>

</div>
</body>
</html>"""
    
    return html


# ---------------------
# EMAIL SENDER
# ---------------------

def send_email(html_content):
    """Send the newsletter via SMTP."""
    email_address = os.getenv("EMAIL_ADDRESS", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    email_to = os.getenv("EMAIL_TO", email_address)
    smtp_server = os.getenv("SMTP_SERVER", "smtp-mail.outlook.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    if not email_address or not email_password:
        print("No email credentials set — saving to newsletter.html instead.")
        # Save to file as fallback
        with open("newsletter.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ Newsletter saved to newsletter.html")
        return False
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Daily Market Brief — {datetime.now().strftime('%b %d, %Y')}"
    msg["From"] = email_address
    msg["To"] = email_to
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, email_password)
        server.sendmail(email_address, email_to, msg.as_string())
        server.quit()
        print(f"✅ Newsletter sent to {email_to}!")
        return True
    except Exception as e:
        print(f"ERROR sending email: {e}")
        with open("newsletter.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Newsletter saved to newsletter.html as fallback.")
        return False


# ---------------------
# MAIN
# ---------------------

def main():
    print("=" * 60)
    print("📊 DAILY MARKET BRIEF — Newsletter Generator")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Fetch market indices
    print("\n[1/6] Fetching market indices...")
    indices_data = fetch_stock_data(list(INDICES.keys()))
    print(f"  ✓ Got data for {len(indices_data)} indices")
    
    # 2. Fetch watchlist
    print("\n[2/6] Fetching your watchlist...")
    watchlist_data = fetch_stock_data(list(WATCHLIST.keys()))
    print(f"  ✓ Got data for {len(watchlist_data)} watchlist stocks")
    
    # 3. Fetch broader movers
    print("\n[3/6] Scanning for top movers...")
    movers_data = fetch_stock_data(MOVERS_UNIVERSE)
    print(f"  ✓ Scanned {len(movers_data)} stocks for movers")
    
    # 4. Fetch market-moving news
    print("\n[4/6] Fetching market-moving news...")
    all_market_news = []
    for query in MARKET_NEWS_QUERIES:
        articles = fetch_news(query, page_size=3)
        all_market_news.extend(articles)
        print(f"  ✓ '{query[:40]}...' → {len(articles)} articles")
    
    # Deduplicate by title
    seen_titles = set()
    market_news = []
    for article in all_market_news:
        if article["title"] not in seen_titles and article["title"] != "[Removed]":
            seen_titles.add(article["title"])
            market_news.append(article)
    print(f"  ✓ Total unique market articles: {len(market_news)}")
    
    # 5. Fetch global macro & sports
    print("\n[5/6] Fetching global macro & sports...")
    global_news = fetch_news(GLOBAL_MACRO_QUERY, page_size=5)
    sports_news = fetch_news(SPORTS_QUERY, page_size=5)
    print(f"  ✓ Global macro: {len(global_news)} | Sports: {len(sports_news)}")
    
    # 6. Build and send
    print("\n[6/6] Building newsletter...")
    vix_value = indices_data.get("^VIX", {}).get("price")
    html = build_html(
        indices_data, watchlist_data, movers_data,
        market_news, global_news, sports_news, vix_value
    )
    print(f"  ✓ Newsletter built ({len(html):,} chars)")
    
    # Send email or save to file
    print("\n📧 Sending/saving newsletter...")
    send_email(html)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
