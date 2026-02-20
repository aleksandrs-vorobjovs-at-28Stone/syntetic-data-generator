import pandas as pd
import numpy as np
import json
import uuid
import random
import yfinance as yf
from datetime import datetime, timedelta

# --- CONFIGURATION for Hackathon (DYNAMIC) ---
# This ensures the data always looks "Live" relative to when you run the script.

# Calculate the Monday of the current week to start the simulation
now = datetime.now()
monday_of_current_week = now - timedelta(days=now.weekday())
START_DATE = monday_of_current_week.replace(hour=8, minute=0, second=0, microsecond=0)

BUSINESS_DAYS = 5    # Simulate Mon-Fri of the CURRENT week
TRADES_PER_DAY = 2000 
OUTPUT_FILE = 'data.json'

def get_live_vix():
    """Fetches real-time VIX or defaults to 16.50"""
    try:
        vix = yf.Ticker("^VIX").history(period="1d")
        return round(float(vix['Close'].iloc[-1]), 2) if not vix.empty else 16.50
    except:
        return 16.50 

def generate_synthetic_data():
    # 1. Load Seed Data
    try:
        with open('seed_engine.json', 'r') as f:
            full_seed = json.load(f)
            ticker_data = full_seed.get("ticker_metadata", {})
            
            # Extract Global Parameters
            sys_efficiency = full_seed.get("systemic_efficiency", 0.9669)
            sys_fail_baseline = max(0.0, 1.0 - sys_efficiency) # ~3.31%
            
            bond_context = full_seed.get("bond_market_context", {})
            bond_daily_vol = bond_context.get("avg_daily_volume_m", 45000)
            bond_liquidity_mult = bond_context.get("liquidity_multiplier", 1.0)

            equity_tickers = [t for t, m in ticker_data.items() if m['asset_class'] == "Equity"]
            fi_tickers = [t for t, m in ticker_data.items() if m['asset_class'] != "Equity"]
            
    except Exception as e:
        print(f"❌ Error loading seeds: {e}")
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

    current_vix = get_live_vix()
    vix_baseline = 15.0
    # Normalize VIX (e.g., 20.0 / 15.0 = 1.33x stress)
    systemic_stress = round(current_vix / vix_baseline, 2)
    
    trades = []
    print(f"🚀 Generating {TRADES_PER_DAY * BUSINESS_DAYS} trades over {BUSINESS_DAYS} days...")
    print(f"📊 Market Stress Factor (VIX): {systemic_stress}x")

    # 3. Simulation Loop
    for day_offset in range(BUSINESS_DAYS):
        current_day_base = START_DATE + timedelta(days=day_offset)
        
        for _ in range(TRADES_PER_DAY):
            # --- A. Selection Logic ---
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
            
            # TOTAL PROBABILITY FORMULA
            # (Base * MarketStress * CP * Liquidity * Time * Size) + SystemicBaseline
            total_fail_prob = (r_base * systemic_stress * r_cp * r_liq * r_time * r_size) + sys_fail_baseline
            
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
                "SettlementDate": (prep_time + timedelta(days=1)).strftime('%Y-%m-%d'), # T+1
                "Asset_Class": asset_class,
                "Asset_ISIN": ticker,
                "Asset_Liquidity_Score": liq_score,       # NEW: 0-1 Scale
                "Direction": direction,
                "Counterparty": cp['name'],
                "Counterparty_Credit_Score": cp['credit_score'], # NEW: 300-850
                "Counterparty_Hist_Fail_Rate": cp['hist_fail_rate'], # NEW: Hist Perf
                "SettlementAmount": amt,                  # NEW: Log-Normal
                "Time_of_Day_Flag": time_flag,            # NEW: Feature for ML
                "Currency": "USD",
                "Status": status,
                "ISO_ReasonCode": reason,
                "Market_Volatility_Factor": systemic_stress # NEW: VIX Metric
            })

    # 4. Sort Chronologically (Crucial for LSTM/Time-Series)
    trades.sort(key=lambda x: x['PreparationDateTime'])
    
    # 5. Export
    df = pd.DataFrame(trades)
    df.to_json(OUTPUT_FILE, orient='records', indent=4)
    df.to_csv('settlements.csv', index=False)
    
    print(f"✅ Success! Generated {len(trades)} trades.")
    print(f"📅 Data sorted from {df['PreparationDateTime'].min()} to {df['PreparationDateTime'].max()}")
    print(f"💾 Saved to {OUTPUT_FILE} and settlements.csv")

if __name__ == "__main__":
    generate_synthetic_data()