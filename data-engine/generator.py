import pandas as pd
import numpy as np
import json
import uuid
import random
import yfinance as yf
import os
from datetime import datetime, timedelta

# --- PATH CONFIGURATION (DYNAMIC) ---
# Automatically resolve the folder where this script lives (e.g., /data-engine)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_FILE = os.path.join(SCRIPT_DIR, 'seed_engine.json')
JSON_FILE = os.path.join(SCRIPT_DIR, 'data.json')
#CSV_FILE = os.path.join(SCRIPT_DIR, 'settlements.csv')

# Calculate the Monday of the current week to start the simulation
now = datetime.now()
monday_of_current_week = now - timedelta(days=now.weekday())
START_DATE = monday_of_current_week.replace(hour=8, minute=0, second=0, microsecond=0)

BUSINESS_DAYS = 5    # Simulate Mon-Fri of the CURRENT week
TRADES_PER_DAY = 2000 

def get_live_vix():
    """Fetches real-time VIX from the Yahoo Finance API or set defaults to 16.50"""
    try:
        vix = yf.Ticker("^VIX").history(period="1d")
        return round(float(vix['Close'].iloc[-1]), 2) if not vix.empty else 16.50
    except:
        return 16.50 

def generate_synthetic_data():
    # 1. Load Seed Data (Uses dynamic path)
    try:
        with open(SEED_FILE, 'r') as f:
            full_seed = json.load(f)
            ticker_data = full_seed.get("ticker_metadata", {})
            
            sys_efficiency = full_seed.get("systemic_efficiency", 0.9669)
            sys_fail_baseline = max(0.0, 1.0 - sys_efficiency) # ~3.31%
            
            bond_context = full_seed.get("bond_market_context", {})
            bond_daily_vol = bond_context.get("avg_daily_volume_m", 45000)
            
            equity_tickers = [t for t, m in ticker_data.items() if m['asset_class'] == "Equity"]
            fi_tickers = [t for t, m in ticker_data.items() if m['asset_class'] != "Equity"]
            
    except Exception as e:
        print(f"❌ Error loading seeds from {SEED_FILE}: {e}")
        return

    # 2. Define Counterparties (With specific Risk Profiles)
    # This maps directly to your "Counterparty Credit Quality" model feature
    counterparties = [
        {"id": "2138006M8651", "name": "JPM_CHASE_NA",       "credit_score": 825, "hist_fail_rate": 0.015},
        {"id": "5493001KJX12", "name": "GOLDMAN_SACHS_INTL", "credit_score": 810, "hist_fail_rate": 0.018},
        {"id": "7LR9S95S8L34", "name": "NOMURA_INTL",        "credit_score": 760, "hist_fail_rate": 0.025},
        {"id": "549300675865", "name": "BARCLAYS_CAPITAL",   "credit_score": 780, "hist_fail_rate": 0.022},
        {"id": "213800VZW961", "name": "BEYOND_ALPHA_HF",    "credit_score": 580, "hist_fail_rate": 0.120}  # High Risk!
    ]

    # We fetche real-time VIX from the Yahoo Finance API
    # We did this only once initially to avoid spamming (fetching the live VIX 10,000 times would instantly get our IP address banned!)
    # We will simulate realistic market fluctuations locally without making extra API calls
    current_vix = get_live_vix()
    vix_baseline = 15.0
    # We rename this to "base" because it will serve as the anchor for our fluctuations
    base_systemic_stress = current_vix / vix_baseline 
    
    trades = []
    print(f"🚀 Generating {TRADES_PER_DAY * BUSINESS_DAYS} trades over {BUSINESS_DAYS} days...")
    print(f"📊 Base Market Stress Factor (VIX): {round(base_systemic_stress, 2)}x")

    # 3. Simulation Loop
    for day_offset in range(BUSINESS_DAYS):
        current_day_base = START_DATE + timedelta(days=day_offset)
        
        for _ in range(TRADES_PER_DAY):
            # --- A. Asset & Counterparty Selection ---
            # 70% Equity, 30% Fixed Income
            if random.random() < 0.70:
                ticker = random.choice(equity_tickers)
            else:
                ticker = random.choice(fi_tickers)
            
            asset_info = ticker_data[ticker]
            asset_class = asset_info.get('asset_class', 'Equity')
            
            # Weighted Choice: Big banks trade more volume than the risky HF
            cp = random.choices(counterparties, weights=[30, 30, 20, 15, 5])[0]

            # --- B. Time Generation (Market Hours vs Cut-off) ---
            # Skew towards end of day (Cut-off risk)
            hour = random.choices(range(8, 17), weights=[5,5,5,5,10,10,10,20,30])[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            prep_time = current_day_base.replace(hour=hour, minute=minute, second=second)
            
            # Feature: Time of Day Flag
            time_flag = "Near_Cutoff" if hour >= 15 else "Market_Hours"

            # --- C. Feature Generation (Explicit for ML) ---
            
            # 1. Asset Liquidity (0-1 Scale)
            # Equities are high (0.8-0.95), Bonds lower (0.3-0.7)
            if asset_class == "Equity":
                liq_score = round(np.random.uniform(0.80, 0.99), 2)
            else:
                liq_score = round(np.random.uniform(0.30, 0.70), 2)

            # 2. Trade Size (Log-Normal)
            is_fi = (asset_class != "Equity")
            mu = 11.5 if is_fi else 10.2
            amt = round(np.random.lognormal(mean=mu, sigma=1.2), 2)
            
            # Bond Cap: Max 0.5% of daily volume
            if is_fi:
                max_realistic = bond_daily_vol * 1_000_000 * 0.005
                amt = min(amt, max_realistic)
            
            # --- D. Probability Calculation ---
            # Factors extracted for clarity
            
            # Risk 1: Ticker Base Risk (from SEC/FINRA)
            r_base = asset_info.get('historical_fail_rate', 0.02)
            
            # Risk 2: Counterparty Credit (Low Score = High Risk)
            # 850 score -> 1.0x (No Penalty)
            # 580 score -> 3.0x (Huge Penalty)
            r_cp = max(1.0, (850 - cp['credit_score']) / 80)
            
            # Risk 3: Liquidity (Low Score = High Risk)
            # Score 0.9 -> 1.0x
            # Score 0.3 -> 2.5x
            r_liq = max(1.0, (1.0 - liq_score) * 4)
            
            # Risk 4: Time (Cut-off pressure)
            r_time = 1.5 if time_flag == "Near_Cutoff" else 1.0
            
            # Risk 5: Size (Big Ticket Penalty)
            r_size = 1.0
            if is_fi and amt > 2_000_000: r_size = 2.0
            elif not is_fi and amt > 5_000_000: r_size = 2.0
            
            # --- MICRO-VOLATILITY JITTER ---
            # Inject a random +/- 5% daily fluctuation to the base VIX stress
            stress_jitter = np.random.normal(0, 0.05)
            trade_systemic_stress = max(0.5, round(base_systemic_stress + stress_jitter, 3))

            # TOTAL PROBABILITY FORMULA
            # (Base * MarketStress * CP * Liquidity * Time * Size) + SystemicBaseline
            total_fail_prob = (r_base * trade_systemic_stress * r_cp * r_liq * r_time * r_size) + sys_fail_baseline
            
            # Cap probability at 98% (Nothing is 100% certain)
            total_fail_prob = min(total_fail_prob, 0.98)

            # --- E. Determine Status ---
            status = "PENF" if random.random() < total_fail_prob else "ACSC"
            direction = random.choice(["DELI", "RECE"])
            
            # Assign Logical Reason Code
            reason = ""
            if status == "PENF":
                if direction == "DELI":
                    # Seller failed to deliver securities
                    reason = "INSU" if liq_score < 0.5 else "LATE"
                else:
                    # Buyer failed to pay cash
                    reason = "CASH" if cp['credit_score'] < 650 else "CLOS"

            # --- F. Build Record ---
            trades.append({
                "UETR": str(uuid.uuid4()),
                "PreparationDateTime": prep_time.isoformat() + "Z",
                "SettlementDate": (prep_time + timedelta(days=1)).strftime('%Y-%m-%d'),
                "Asset_Class": asset_class,
                "Asset_ISIN": ticker,
                "Asset_Liquidity_Score": liq_score,
                "Direction": direction,
                "Counterparty": cp['name'],
                "Counterparty_Credit_Score": cp['credit_score'],
                "Counterparty_Hist_Fail_Rate": cp['hist_fail_rate'],
                "SettlementAmount": amt,
                "Time_of_Day_Flag": time_flag,
                "Currency": "USD",
                "Status": status,
                "ISO_ReasonCode": reason,
                "Market_Volatility_Factor": trade_systemic_stress
            })

    # 4. Sort Chronologically (Crucial for the real-time Python Streamer playback)
    trades.sort(key=lambda x: x['PreparationDateTime'])
    
    # 5. Export (Uses dynamic paths)
    df = pd.DataFrame(trades)
    df.to_json(JSON_FILE, orient='records', indent=4)
    #df.to_csv(CSV_FILE, index=False)
    
    print(f"✅ Success! Generated {len(trades)} trades.")
    #print(f"💾 Saved to {JSON_FILE} and {CSV_FILE}")
    print(f"💾 Saved to {JSON_FILE}")

if __name__ == "__main__":
    generate_synthetic_data()