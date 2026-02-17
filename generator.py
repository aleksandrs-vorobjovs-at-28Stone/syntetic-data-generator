import pandas as pd
import numpy as np
import json
import uuid
import datetime
import random
import yfinance as yf

def get_live_vix():
    """Fetches real-time VIX baseline or uses a default if API fails."""
    try:
        # Fixed: Explicitly selecting the scalar value to avoid FutureWarnings
        vix_df = yf.download("^VIX", period="1d", interval="1m", progress=False)
        if not vix_df.empty:
            vix_series = vix_df['Close']
            # Accessing the last value as a scalar
            vix_value = vix_series.values[-1]
            return round(float(vix_value), 2)
        return 16.50
    except Exception as e:
        print(f"VIX Fetch Info: Using default baseline due to: {e}")
        return 16.50 

def generate_synthetic_data(num_trades=10000):
    # 1. Load Seed Data safely
    try:
        with open('seed_engine.json', 'r') as f:
            raw_seed = json.load(f)
            if isinstance(raw_seed, dict):
                temp_list = list(raw_seed.values())
            else:
                temp_list = raw_seed
            seed_data = [item for item in temp_list if isinstance(item, dict)]
    except Exception as e:
        print(f"Error loading seed data: {e}")
        return

    # 2. Setup Market Baseline (Systemic Stress)
    current_vix = get_live_vix()
    vix_baseline = 15.0
    systemic_stress = current_vix / vix_baseline

    # 3. Reference Data for Counterparties
    leis = [
        ("2138006M8651", "JPM_CHASE_NA"),
        ("5493001KJX12", "GOLDMAN_SACHS_INTL"),
        ("7LR9S95S8L34", "NOMURA_INTL"),
        ("549300675865", "BARCLAYS_CAPITAL"),
        ("213800VZW961", "BEYOND_ALPHA_HF")
    ]

    trades = []
    
    # 4. Generation Loop
    print(f"Starting generation of {num_trades} trades with Asset Class and Direction...")
    for _ in range(num_trades):
        # Pick a valid asset
        asset = random.choice(seed_data)
        lei_id, lei_name = random.choice(leis)
        
        # --- NEW: Logic for Asset Class ---
        # If the ticker has a '-' or is longer than 5 chars, we treat it as a Bond 
        # (mimicking TRACE format), otherwise Equity.
        ticker = asset.get('ticker', 'UNKNOWN')
        asset_class = "Corporate Bond" if ("-" in ticker or len(ticker) > 5) else "Equity"
        
        # --- NEW: Logic for Direction (ISO 20022 terms) ---
        # DELI = Delivery (Sell), RECE = Receive (Buy)
        direction = random.choice(["DELI", "RECE"])
        
        # --- Micro-Fluctuations ---
        micro_jitter = np.random.uniform(-0.04, 0.04)
        trade_vol_factor = round(systemic_stress + micro_jitter, 3)

        # --- Probability Calculation ---
        base_risk = asset.get('historical_fail_rate', 0.02)
        hour = random.choices(range(8, 18), weights=[5,5,5,5,5,5,5,20,40,10])[0]
        prep_time = f"{hour:02d}:{random.randint(0, 59):02d}:00Z"
        
        # Risk Multipliers
        time_multiplier = 4.5 if hour >= 15 else 1.0
        amt = round(np.random.lognormal(mean=10.5, sigma=1.2), 2)
        size_multiplier = 3.0 if amt > 5000000 else 1.0
        
        # Final Status
        fail_prob = base_risk * trade_vol_factor * time_multiplier * size_multiplier
        status = "PENF" if random.random() < fail_prob else "ACSC"
        reason = random.choice(["INSU", "LATE", "CASH", "CLOS"]) if status == "PENF" else ""

        # 5. Build Record
        trades.append({
            "UETR": str(uuid.uuid4()),
            "InstructingParty_LEI": lei_id,
            "Counterparty": lei_name,
            "Direction": direction,
            "Asset_Class": asset_class,
            "Asset_ISIN": ticker,
            "SettlementAmount": amt,
            "Currency": "USD",
            "PreparationDateTime": prep_time,
            "SettlementCycle": "T+1",
            "Status": status,
            "ISO_ReasonCode": reason,
            "Market_Volatility_Factor": trade_vol_factor
        })

    # 6. Save Files
    df = pd.DataFrame(trades)
    df.to_json('data.json', orient='records', indent=4)
    df.to_csv('settlements.csv', index=False)
    print(f"Success: Generated 10,000 trades with enriched fields.")

if __name__ == "__main__":
    generate_synthetic_data()