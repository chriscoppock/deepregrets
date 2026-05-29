import warnings
import yfinance as yf
import pandas as pd
from GoogleNews import GoogleNews
import ollama
import json
import sqlite3
from datetime import datetime, timedelta

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", category=FutureWarning)

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
conn = sqlite3.connect("trading_history.db")
cursor = conn.cursor()

# Upgraded schema tracking columns for comprehensive data logging
cursor.execute("""
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TEXT,
    ticker TEXT,
    close_price REAL,
    sma_10 REAL,
    deviation REAL,
    sentiment TEXT,
    reasoning TEXT,
    investment_amount REAL,
    macro_risk TEXT,
    growth_viability TEXT
)
""")
conn.commit()

# ==========================================
# INTERACTIVE INPUTS WITH VALIDATION
# ==========================================
user_ticker = input("Enter a stock ticker to scan (e.g., MU, NVDA): ").upper()

while True:
    cash_input_str = input("Enter the cash amount to simulate investing (e.g., 500, 5000): ")
    try:
        investment_amount = float(cash_input_str)
        if investment_amount <= 0:
            print("[-] Investment must be a positive number greater than $0.")
            continue
        break
    except ValueError:
        print("[-] Invalid number. Please enter a valid cash amount.")

valid_date = False
while not valid_date:
    user_date_str = input("Enter historical purchase date (MM/DD/YYYY): ")
    try:
        input_date = datetime.strptime(user_date_str, "%m/%d/%Y")
        start_date_yf = input_date.strftime("%Y-%m-%d")
        buffer_start = (input_date - timedelta(days=60)).strftime("%Y-%m-%d")
        buffer_end = (input_date + timedelta(days=5)).strftime("%Y-%m-%d")
        valid_date = True
    except ValueError:
        print("[-] Invalid format. Please use MM/DD/YYYY exactly (e.g., 10/16/2011).")

print(f"\n[+] Connecting to market data logs for {user_ticker} around {user_date_str}...")

try:
    historical_df = yf.download(user_ticker, start=buffer_start, end=buffer_end, progress=False)
    
    if historical_df is None or historical_df.empty:
        print(f"[-] Error: No market data returned for ticker '{user_ticker}' during that timeframe.")
        exit()

    if isinstance(historical_df.columns, pd.MultiIndex):
        historical_df.columns = historical_df.columns.get_level_values(0)

    historical_df['10_Day_SMA'] = historical_df['Close'].rolling(window=10).mean()
    period_high = float(historical_df['High'].max())
    period_low = float(historical_df['Low'].min())

    if start_date_yf in historical_df.index.strftime('%Y-%m-%d'):
        target_row = historical_df.loc[start_date_yf]
    else:
        target_row = historical_df.iloc[-1]
        start_date_yf = target_row.name.strftime('%Y-%m-%d')
        print(f"[*] Note: Selected date was a market holiday. Using closest trading day: {start_date_yf}")

    historical_close = float(target_row['Close'])
    historical_sma = float(target_row['10_Day_SMA'])
    percent_deviation = ((historical_close - historical_sma) / historical_sma) * 100

    print(f"[+] Fetching current live asset price metrics for {user_ticker} today...")
    current_df = yf.download(user_ticker, period="1d", progress=False)
    if isinstance(current_df.columns, pd.MultiIndex):
        current_df.columns = current_df.columns.get_level_values(0)
    current_price = float(current_df['Close'].iloc[-1])

    print(f"[+] Scraping live web headlines for {user_ticker} from Google News...")
    googlenews = GoogleNews(lang='en', region='US')
    googlenews.search(f"{user_ticker} stock")
    raw_results = googlenews.results(sort=True)
    live_headlines = []
    
    for result in raw_results:
        title = result.get('title')
        if title and isinstance(title, str) and title not in live_headlines:
            live_headlines.append(title)
        if len(live_headlines) == 3:
            break

    if not live_headlines:
        live_headlines = ["Market trading volumes remain steady for this sector."]

    print("\n--- RECENT LIVE HEADLINES FOUND ---")
    for idx, headline in enumerate(live_headlines, 1):
        print(f" {idx}. {headline}")

    # ==========================================
    # UPGRADED ADVANCED AI RISK PROMPT ENGINE
    # ==========================================
    print(f"\n[+] Executing advanced Risk Factor Analysis via local Llama3...")
    headlines_text = "\n".join([f"- {h}" for h in live_headlines])
    
    prompt = f"""
    You are an elite quantitative financial risk analyst. Evaluate these recent headlines for {user_ticker}:
    {headlines_text}
    
    Assess market sentiment, macro ecosystem threats (like sector bubbles or pullbacks), and long-term asset growth stability.
    
    You must output strictly a single valid JSON object matching this blueprint layout structure exactly:
    {{
        "sentiment": "BULLISH" or "BEARISH" or "NEUTRAL",
        "confidence_score": an integer from -3 to 3,
        "macro_risk_rating": "LOW" or "MEDIUM" or "HIGH",
        "growth_viability": "LOW" or "MEDIUM" or "HIGH",
        "ai_context_analysis": "A concise one-sentence core rationale of your structural risk evaluation."
    }}
    Do not output markdown codeblocks, notes, wrapper formatting or introductory text. Output raw JSON only.
    """

    response = ollama.generate(model='llama3', prompt=prompt, format='json')
    ai_data = json.loads(response['response'].strip())
    
    llm_sentiment = ai_data.get("sentiment", "NEUTRAL").upper()
    ai_score = ai_data.get("confidence_score", 0)
    ai_macro_risk = ai_data.get("macro_risk_rating", "MEDIUM").upper()
    ai_growth_viability = ai_data.get("growth_viability", "MEDIUM").upper()
    ai_reasoning = ai_data.get("ai_context_analysis", "No context provided.")

    # Investment Simulator Math
    shares_held = investment_amount / historical_close
    current_portfolio_value = shares_held * current_price
    net_roi_dollars = current_portfolio_value - investment_amount
    percent_roi = (net_roi_dollars / investment_amount) * 100

    # --- THE COGNITIVE RISK SIMULATION DASHBOARD ---
    print("\n" + "=" * 60)
    print(f" ADVANCED COGNITIVE RISK & BACKTEST REPORT: {user_ticker}")
    print("=" * 60)
    print(f" Historical Purchase Date:  {start_date_yf}")
    print(f" Historical Close Price:     ${historical_close:.2f}")
    print(f" 10-Day Moving Avg Then:    ${historical_sma:.2f} ({percent_deviation:+.2f}%)")
    print(f" Current Price Today:       ${current_price:.2f}")
    print("-" * 60)
    print(f" AI Market Sentiment:       {llm_sentiment} (Confidence: {ai_score}/3)")
    print(f" Macro Sector Risk Threat:  {ai_macro_risk}")
    print(f" Asset Growth Viability:    {ai_growth_viability}")
    print(f" Risk Rationale Metrics:    {ai_reasoning}")
    print("-" * 60)
    print(f" Simulating ${investment_amount:,.2f} Investment on {start_date_yf}:")
    print(f" Total Shares Purchased:     {shares_held:.4f} shares")
    print(f" Current Asset Value:        ${current_portfolio_value:.2f}")
    print(f" Net Performance Return:     {net_roi_dollars:+.2f} ({percent_roi:+.2f}%)")
    print("=" * 60)

    # --- SAVE TO UPGRADED DATABASE ---
    print("[+] Logging telemetry risk record to trading_history.db...")
    cursor.execute("""
        INSERT INTO scans (scan_date, ticker, close_price, sma_10, deviation, sentiment, reasoning, investment_amount, macro_risk, growth_viability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (start_date_yf, user_ticker, historical_close, historical_sma, percent_deviation, llm_sentiment, ai_reasoning, investment_amount, ai_macro_risk, ai_growth_viability))
    
    conn.commit()
    print("[+] Database write successful. Log secured.")

except Exception as e:
    print(f"[-] An unexpected error occurred: {e}")

finally:
    conn.close()