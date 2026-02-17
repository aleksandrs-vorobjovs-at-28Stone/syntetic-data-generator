import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import uuid
import os

# --- CONFIGURATION & MAPPING ---
# These counterparties have specific risk profiles for your ML model to discover.
COUNTERPARTIES = [
    {"LEI": "5493003020A1", "Name": "JPM_CHASE", "RiskWeight": 0.85},
    {"LEI": "W22LROWCHM24", "Name": "GOLDMAN_SACHS", "RiskWeight": 0.90},
    {"LEI": "815600H98012", "Name": "BARCLAYS_CAP", "RiskWeight": 1.15},
    {"LEI": "5299000W225M", "Name": "NOMURA_INTL", "RiskWeight": 1.60}, # Higher risk
    {"LEI": "2138006M8651", "Name": "BEYOND_ALPHA_HF", "RiskWeight": 2.50} # High risk outlier
]

def get_live_vix():
    """Fetches real-time market stress via Yahoo Finance."""
    try:
        vix = yf.Ticker("^VIX").fast_info['last_price']
        return vix
    except:
        return 22.0 # Standard stressed baseline

def generate_api_data():
    # 1. Load the Calibration Brain
    if not os.path.exists('seed_engine.json'):
        print("Error: seed_engine.json not found.")
        return
    
    with open('seed_engine.json', 'r') as f:
        seeds = json.load(f)

    vix = get_live_vix()
    vol_impact = max(1, vix / 20)
    ticker_list = list(seeds['ticker_stress_scores'].keys())
    
    # Fallback if ticker list is empty
    if not ticker_list:
        ticker_list = ["AAPL", "TSLA", "MSFT", "CORP_BOND_B", "CORP_BOND_AAA"]

    data = []
    print(f"Generating 10,000 trades... Market Stress (VIX Impact): {vol_impact:.2f}x")

    # 2. Generate 10,000 Trades
    for _ in range(10000):
        asset = np.random.choice(ticker_list)
        cp = np.random.choice(COUNTERPARTIES)
        is_bond = "BOND" in asset or len(asset) > 6 
        
        # --- FEATURE ENGINEERING (Authentic Variables) ---
        # A. Settlement Amount (Log-normal: most are small, some are huge)
        par_value = round(np.random.lognormal(mean=11.5, sigma=1.6), 2)
        
        # B. Execution Time (Concentrated near 16:00 UTC market cut-off)
        hour = np.random.choice([9, 10, 11, 12, 13, 14, 15, 15, 15]) 
        exec_time = f"{hour:02d}:{np.random.randint(0,59):02d}:00Z"

        # --- RISK ENGINE (The "Predictive Signal") ---
        base_fail_rate = 1 - seeds['systemic_efficiency']
        ticker_score = seeds['ticker_stress_scores'].get(asset, 1.0)
        
        # Non-linear multipliers (Gamma Stress)
        size_stress = 1.9 if par_value > 2500000 else 1.0
        time_stress = 2.5 if hour >= 15 else 1.0 # High risk if close to cut-off
        
        # Probability calculation
        fail_p = base_fail_rate * pow(ticker_score, 1.5) * cp['RiskWeight'] * vol_impact * size_stress * time_stress
        
        if is_bond:
            fail_p *= seeds['bond_market']['liquidity_multiplier']
        
        # Cap for plausibility
        fail_p = min(fail_p, 0.20)
        is_failed = np.random.binomial(1, fail_p)

        # 3. ISO 20022 MAPPING
        status = "PENF" if is_failed else "ACSC"
        reason = np.random.choice(["INSU", "LATE", "CASH", "CMIS"]) if is_failed else ""
        
        data.append({
            "UETR": str(uuid.uuid4()), # Unique End-to-End Reference
            "InstructingParty_LEI": cp['LEI'],
            "Counterparty": cp['Name'],
            "Asset_ISIN": asset,
            "SettlementAmount": par_value,
            "Currency": "USD",
            "PreparationDateTime": exec_time,
            "SettlementCycle": "T+1" if not is_bond else "T+2",
            "Status": status,
            "ISO_ReasonCode": reason,
            "Market_Volatility_Factor": round(vol_impact, 2)
        })

    # 4. Save Outputs
    df = pd.DataFrame(data)
    
    # JSON for the Dashboard
    df.to_json('data.json', orient='records', indent=4)
    # CSV for the ML Predictive Model
    df.to_csv('settlements.csv', index=False)
    
    print("Generation complete: data.json and settlements.csv updated.")

if __name__ == "__main__":
    generate_api_data()