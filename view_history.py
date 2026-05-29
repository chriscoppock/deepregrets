import sqlite3
import pandas as pd
import yfinance as yf
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

print("[+] Connecting to trading_history.db...")

try:
    conn = sqlite3.connect("trading_history.db")
    
    # 1. Pull the upgraded data layout out of the database
    query = "SELECT * FROM scans"
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("[-] The database is currently empty. Run main.py first to log some simulations!")
    else:
        print("[+] Fetching live up-to-the-minute market quotes for backtesting...")
        
        # 2. Extract unique tickers for live market evaluation
        unique_tickers = df['ticker'].unique().tolist()
        current_data = yf.download(unique_tickers, period="1d", progress=False)
            
        # Hardened multi-ticker data extraction mapping
        live_prices = {}
        for ticker in unique_tickers:
            try:
                if isinstance(current_data.columns, pd.MultiIndex):
                    live_prices[ticker] = float(current_data.loc[:, ('Close', ticker)].iloc[-1])
                else:
                    live_prices[ticker] = float(current_data['Close'].iloc[-1])
            except Exception:
                live_prices[ticker] = 0.0

        # 3. Process the math engine rows using the logged dynamic investment values
        live_prices_col = []
        net_roi_dollars_col = []
        percent_roi_col = []
        
        for idx, row in df.iterrows():
            ticker = row['ticker']
            hist_price = float(row['close_price'])
            
            # FIX: Pull the saved dynamic capital value instead of assuming $1,000
            principal = float(row.get('investment_amount', 1000.0))
            
            current_price_today = live_prices.get(ticker, 0.0)
            
            shares_purchased = principal / hist_price
            current_value = shares_purchased * current_price_today
            net_profit_loss = current_value - principal
            pct_return = (net_profit_loss / principal) * 100
            
            live_prices_col.append(current_price_today)
            net_roi_dollars_col.append(net_profit_loss)
            percent_roi_col.append(pct_return)
            
        df['Current Price'] = live_prices_col
        df['Net Profit/Loss'] = net_roi_dollars_col
        df['Total ROI %'] = percent_roi_col

        # --- THE PORTFOLIO RISK & PERFORMANCE DASHBOARD ---
        print("\n" + "=" * 130)
        print("                         LIVE PORTFOLIO METRICS & ADVANCED RISK LOG")
        print("=" * 130)
        
        display_df = df.rename(columns={
            'scan_date': 'Purchased',
            'ticker': 'Stock',
            'close_price': 'Hist Price',
            'investment_amount': 'Principal',
            'sentiment': 'AI Sent',
            'macro_risk': 'Macro Risk',
            'growth_viability': 'Viability'
        })
        
        # Isolate the core metrics + our new AI risk assessment matrix targets
        columns_to_show = ['Purchased', 'Stock', 'Principal', 'Hist Price', 'Current Price', 'AI Sent', 'Macro Risk', 'Viability', 'Net Profit/Loss', 'Total ROI %']
        
        # Map neat currency and math layouts onto our display dataframe
        formatted_df = display_df[columns_to_show].copy()
        formatted_df['Principal'] = formatted_df['Principal'].map('${:,.2f}'.format)
        formatted_df['Hist Price'] = formatted_df['Hist Price'].map('${:,.2f}'.format)
        formatted_df['Current Price'] = formatted_df['Current Price'].map('${:,.2f}'.format)
        formatted_df['Net Profit/Loss'] = formatted_df['Net Profit/Loss'].map('${:+,.2f}'.format)
        formatted_df['Total ROI %'] = formatted_df['Total ROI %'].map('{:+,.2f}%'.format)
        
        print(formatted_df.to_string(index=False))
        print("=" * 130)
        
        total_simulations = len(df)
        total_net_gains = sum(net_roi_dollars_col)
        print(f" Aggregate Portfolio Count: {total_simulations} Simulations")
        print(f" Combined Net Performance:   ${total_net_gains:+,.2f} overall across all virtual investments.")
        print("=" * 130)

except Exception as e:
    print(f"[-] Database live processing failed: {e}")

finally:
    conn.close()