import warnings
import yfinance as yf
import pandas as pd
import json
import sqlite3
import hashlib  # Used for secure cryptographic password hashing
import streamlit as st
from datetime import datetime, timedelta

# Import official Google GenAI components & Pydantic
from google import genai
from google.genai import types
from pydantic import BaseModel

import os

client = genai.Client()

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(page_title="Gemini Multi-User Risk Agent", page_icon="📈", layout="wide")

# ==========================================
# DEFINE THE ENFORCED GEMINI JSON SCHEMA
# ==========================================
class RiskAssessment(BaseModel):
    sentiment: str
    confidence_score: int
    macro_risk_rating: str
    growth_viability: str
    ai_context_analysis: str

# Initialize the Gemini Client
try:
    client = genai.Client()
except Exception as e:
    st.error("Could not initialize Gemini Client. Make sure GEMINI_API_KEY is set in your environment variables.")

# ==========================================
# HARDENED DATABASE LOGIC FUNCTIONS
# ==========================================
def init_db():
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    
    # 1. Create Users authentication tracking table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)
    
    # 2. Upgraded scans table to include user_id relation mapping (11 columns total)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        scan_date TEXT,
        ticker TEXT,
        close_price REAL,
        sma_10 REAL,
        deviation REAL,
        sentiment TEXT,
        reasoning TEXT,
        investment_amount REAL,
        macro_risk TEXT,
        growth_viability TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = sqlite3.connect("trading_history.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[1] == hash_password(password):
        return row[0]
    return None

def log_to_db(user_id, date, ticker, price, sma, dev, sentiment, reasoning, principal, macro, viability):
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans (user_id, scan_date, ticker, close_price, sma_10, deviation, sentiment, reasoning, investment_amount, macro_risk, growth_viability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, date, ticker, price, sma, dev, sentiment, reasoning, principal, macro, viability))
    conn.commit()
    conn.close()

def get_user_history_df(user_id):
    conn = sqlite3.connect("trading_history.db")
    df = pd.read_sql_query("SELECT * FROM scans WHERE user_id = ? ORDER BY id DESC", conn, params=(user_id,))
    conn.close()
    return df

def clear_user_db(user_id):
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# AUTHENTICATION GATE & SESSION MANAGEMENT
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔒 Quantitative Risk Platform Secure Gateway")
    st.markdown("Please authenticate your user account or sign up for a local account profile to persist backtest telemetry tracks.")
    st.write("---")
    
    auth_tab, register_tab = st.tabs(["🔑 Sign In", "📝 Create Secure Account"])
    
    with auth_tab:
        login_user = st.text_input("Username", key="login_user_input").strip()
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        if st.button("Authorize Session"):
            uid = authenticate_user(login_user, login_pass)
            if uid:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.username = login_user
                st.toast(f"Welcome back, {login_user}!", icon="🔓")
                st.rerun()
            else:
                st.error("Invalid credentials block. Check entry details and try again.")
                
    with register_tab:
        reg_user = st.text_input("Choose Username", key="reg_user_input").strip()
        reg_pass = st.text_input("Choose Secure Password", type="password", key="reg_pass_input")
        if st.button("Generate Profile"):
            if len(reg_user) < 3 or len(reg_pass) < 4:
                st.warning("Validation failure: Username must be ≥ 3 chars, Password must be ≥ 4 chars.")
            else:
                if register_user(reg_user, reg_pass):
                    st.success("Account profile successfully secured! Sign in to continue.")
                else:
                    st.error("Registration error: That username is already reserved inside local system storage.")
    st.stop()

# ==========================================
# SIDEBAR CONTROL FOR AUTHORIZED SESSIONS
# ==========================================
st.sidebar.title(f"👤 Session: {st.session_state.username}")
if st.sidebar.button("🚪 Terminate Session & Log Out"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("🎮 Agent Control Panel")

user_ticker = st.sidebar.text_input("Asset Ticker Symbol", value="BTC-USD").upper().strip()
investment_amount = st.sidebar.number_input("Capital Investment Principal ($)", min_value=10.0, value=1000.0, step=100.0)
selected_date = st.sidebar.date_input("Historical Purchase Date", value=datetime(2016, 10, 3))
bulk_limit = st.sidebar.slider("Historical Event Ingestion Volume", min_value=5, max_value=20, value=15, step=5)

run_analysis = st.sidebar.button("🚀 Run Cognitive Analytics")

st.sidebar.write("---")
st.sidebar.subheader("⚠️ Danger Zone")
confirm_wipe = st.sidebar.checkbox("I am sure I want to wipe my ledger profile")

if st.sidebar.button("🗑️ Clear My Ledger History", disabled=not confirm_wipe):
    clear_user_db(st.session_state.user_id)
    st.toast("Your personal tracking profile cleared successfully!", icon="🔥")
    st.rerun()

# ==========================================
# MAIN DASHBOARD INTERFACE LAYOUT (AUTHENTICATED)
# ==========================================
st.title("📈 Gemini Financial Backtester & Risk Agent")
st.markdown(f"Welcome back, **{st.session_state.username}**. Blending price calculations with cloud-based Gemini analytics.")
st.write("---")

if run_analysis:
    if not user_ticker:
        st.error("Please enter a valid stock or crypto ticker symbol first.")
    else:
        start_date_yf = selected_date.strftime("%Y-%m-%d")
        buffer_start = (selected_date - timedelta(days=60)).strftime("%Y-%m-%d")
        buffer_end = (selected_date + timedelta(days=5)).strftime("%Y-%m-%d")
        
        with st.spinner(f"Running chronological cloud pipeline for {user_ticker}..."):
            try:
                # Historical market ingestion
                historical_df = yf.download(user_ticker, start=buffer_start, end=buffer_end, progress=False)
                if historical_df is None or historical_df.empty:
                    st.error(f"No market data returned for '{user_ticker}' during that timeframe.")
                    st.stop()
                    
                if isinstance(historical_df.columns, pd.MultiIndex):
                    historical_df.columns = historical_df.columns.get_level_values(0)

                historical_df['10_Day_SMA'] = historical_df['Close'].rolling(window=10).mean()
                
                # Dynamic index matching safety loop
                available_dates = historical_df.index.strftime('%Y-%m-%d')
                if start_date_yf in available_dates:
                    target_row = historical_df.loc[start_date_yf]
                else:
                    closest_idx = historical_df.index.get_indexer([pd.to_datetime(start_date_yf)], method='nearest')[0]
                    target_row = historical_df.iloc[closest_idx]
                    start_date_yf = target_row.name.strftime('%Y-%m-%d')
                    st.warning(f"Note: Selected date was a holiday/weekend. Using closest trading day: **{start_date_yf}**")

                historical_close = float(target_row['Close'].iloc[0]) if isinstance(target_row['Close'], pd.Series) else float(target_row['Close'])
                historical_sma = float(target_row['10_Day_SMA'].iloc[0]) if isinstance(target_row['10_Day_SMA'], pd.Series) else float(target_row['10_Day_SMA'])
                percent_deviation = ((historical_close - historical_sma) / historical_sma) * 100

                # Ingest Modern Live Value Quote (Single isolated fetch)
                current_df = yf.download(user_ticker, period="1d", progress=False)
                if isinstance(current_df.columns, pd.MultiIndex):
                    current_df.columns = current_df.columns.get_level_values(0)
                current_price = float(current_df['Close'].iloc[-1])

                # Chronological Prompt Engine
                prompt = f"""
                You are an elite quantitative financial risk analyst conducting a historical backtest for the asset {user_ticker}.
                The user is simulating a capital allocation on the exact date: **{start_date_yf}**.
                
                Step 1: Retrieve from your internal deep historical knowledge base a bulk comprehensive array of up to {bulk_limit} major market events, news headlines, development tracking milestones, scaling debates, macroeconomic indicators, or regulatory actions that were actively dominating the media ecosystem or happening around **{start_date_yf}** for {user_ticker}.
                
                Step 2: Systematically evaluate that specific historical era data matrix:
                1. Identify conflicting viewpoints from that specific time window (e.g., weigh technological wins or adoption growth against hacks, market anxieties, or liquidations).
                2. Evaluate the historical consensus. Was the overarching market momentum back on {start_date_yf} genuinely BULLISH, BEARISH, or highly divided and NEUTRAL?
                3. Quantify macro ecosystem risk threat levels and asset growth sustainability *at that exact moment in history* based on the environment then.
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RiskAssessment,
                    ),
                )
                
                ai_data = json.loads(response.text)
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

                log_to_db(st.session_state.user_id, start_date_yf, user_ticker, historical_close, historical_sma, percent_deviation, llm_sentiment, ai_reasoning, investment_amount, ai_macro_risk, ai_growth_viability)

                # Rendering Components
                st.subheader(f"📊 Quantitative Asset Valuation Dashboard for {user_ticker}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Historical Price (Then)", f"${historical_close:,.2f}", f"{percent_deviation:+.2f}% from SMA")
                col2.metric("Current Price (Today)", f"${current_price:,.2f}")
                col3.metric("Current Net Returns", f"${net_roi_dollars:+,.2f}", f"{percent_roi:+.2f}% ROI")
                col4.metric("Total Shares Accumulated", f"{shares_held:,.4f}")

                st.write("---")
                st.subheader(f"🧠 Chronological Risk Assessment Matrix ({bulk_limit} Historical Points Evaluated)")
                sent_col, risk_col, via_col = st.columns(3)
                sent_col.info(f"**AI Sentiment Then:** {llm_sentiment} (Confidence: {ai_score}/3)")
                risk_col.warning(f"**Macro Threat Level Then:** {ai_macro_risk}")
                via_col.success(f"**Asset Growth Viability Then:** {ai_growth_viability}")
                st.markdown(f"**Historical Era Consensus Rationale:** *{ai_reasoning}*")

            except Exception as e:
                st.error(f"An unexpected crash occurred inside the data pipeline: {e}")

# ==========================================
# METRICS OVERVIEW (BULLETPROOF INDEPENDENT LOOKUP)
# ==========================================
st.write("---")
st.subheader("💰 Lifetime Simulated Portfolio Performance Summary")

history_df = get_user_history_df(st.session_state.user_id)

if history_df.empty:
    st.info("No past telemetry logs saved under this user account profile yet. Run an analysis to populate tracks.")
else:
    with st.spinner("Calculating total live portfolio gains..."):
        try:
            unique_tickers = history_df['ticker'].unique().tolist()
            
            # --- ULTIMATE ZERO-NAN SINGLE-TICKER FETCH LOOP ---
            live_prices_lookup = {}
            for ticker in unique_tickers:
                try:
                    ticker_data = yf.download(ticker, period="1d", progress=False)
                    if isinstance(ticker_data.columns, pd.MultiIndex):
                        ticker_data.columns = ticker_data.columns.get_level_values(0)
                    live_prices_lookup[ticker] = float(ticker_data['Close'].iloc[-1])
                except Exception:
                    live_prices_lookup[ticker] = 0.0

            total_principal_invested = 0.0
            total_current_portfolio_value = 0.0
            
            for idx, row in history_df.iterrows():
                ticker = row['ticker']
                hist_close_price = float(row['close_price'])
                saved_principal = float(row.get('investment_amount', 1000.0))
                live_price_today = live_prices_lookup.get(ticker, 0.0)
                
                # Performance Math Execution
                if hist_close_price > 0 and live_price_today > 0:
                    shares_bought = saved_principal / hist_close_price
                    current_value = shares_bought * live_price_today
                else:
                    current_value = saved_principal
                
                total_principal_invested += saved_principal
                total_current_portfolio_value += current_value
                
            total_net_profit_loss = total_current_portfolio_value - total_principal_invested
            lifetime_roi_pct = (total_net_profit_loss / total_principal_invested) * 100 if total_principal_invested > 0 else 0.0
            
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Virtual Capital Invested", f"${total_principal_invested:,.2f}")
            m_col2.metric("Current Active Value Today", f"${total_current_portfolio_value:,.2f}")
            m_col3.metric("Net Lifetime Earnings Return", f"${total_net_profit_loss:+,.2f}", f"{lifetime_roi_pct:+.2f}% Overall Return")
            
        except Exception as e:
            st.error(f"Could not compute historical matrix totals: {e}")

# ==========================================
# RENDER THE USER-ISOLATED HISTORICAL LEDGER
# ==========================================
st.write("---")
st.subheader("📜 Saved Local Simulation History Ledger")

if not history_df.empty:
    clean_history = history_df.rename(columns={
        'scan_date': 'Purchase Date',
        'ticker': 'Asset',
        'close_price': 'Hist Close ($)',
        'investment_amount': 'Principal ($)',
        'sentiment': 'AI Sentiment',
        'macro_risk': 'Macro Threat',
        'growth_viability': 'Viability Rating',
        'reasoning': 'Core Risk Analysis'
    })
    st.dataframe(clean_history[['Purchase Date', 'Asset', 'Principal ($)', 'Hist Close ($)', 'AI Sentiment', 'Macro Threat', 'Viability Rating', 'Core Risk Analysis']], width='stretch')