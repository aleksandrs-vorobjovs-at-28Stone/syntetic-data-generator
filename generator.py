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
        # Fixed: Using .iloc[-1] and explicitly converting to float to avoid FutureWarnings
        vix_df = yf.download("^VIX", period="1d", interval="1m", progress=False)
        if not vix_df.empty:
            vix_value = vix_df['Close'].iloc[-1]
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
            # Ensure we have a list for random.choice, even if JSON is index-oriented
            if isinstance(raw_seed, dict):
                seed_data = list(raw_seed.values())
            else:
                seed_data = raw_seed
    except FileNotFoundError:
        print("Error: seed_engine.json not found. Please ensure it exists in the root.")
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
    print(f"Starting generation of {num_trades} trades...")
    for _ in range(num_trades):
        asset = random.choice(seed_data)
        lei_id, lei_name = random.choice(leis)
        
        # --- Injecting Micro-Fluctuations (Noise) ---
        # Unique jitter per trade between -0.04 and +0.04
        micro_jitter = np.random.uniform(-0.04, 0.04)
        trade_vol_factor = round(systemic_stress + micro_jitter, 3)

        # --- Probability of Failure Calculation ---
        # Base risk from processed SEC/FINRA seeds
        base_risk = asset.get('historical_fail_rate', 0.02)
        
        # Factor A: Time Stress (Late trades near 16:00 cut-off fail more)
        # Weighted hours: 15:00 and 16:00 are highest risk
        hour = random.choices(range(8, 18), weights=[5,5,5,5,5,5,5,20,40,10])[0]
        minute = random.randint(0, 59)
        prep_time = f"{hour:02d}:{minute:02d}:00Z"
        
        time_multiplier = 4.5 if hour >= 15 else 1.0
        
        # Factor B: Trade Size (Log-normal distribution for financial realism)
        amt = round(np.random.lognormal(mean=10.5, sigma=1.2), 2)
        size_multiplier = 3.0 if amt > 5000000 else 1.0
        
        # Final Failure Probability logic
        fail_prob = base_risk * trade_vol_factor * time_multiplier * size_multiplier
        
        # Determine Status
        status = "PENF" if random.random() < fail_prob else "ACSC"
        
        # Assign ISO Reason Code if failed
        reason = ""
        if status == "PENF":
            reason = random.choice(["INSU", "LATE", "CASH", "CLOS"])

        # 5. Build Record
        trades.append({
            "UETR": str(uuid.uuid4()),
            "InstructingParty_LEI": lei_id,
            "Counterparty": lei_name,
            "Asset_ISIN": asset.get('ticker', 'UNKNOWN'),
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
    
    # JSON for Web Dashboard
    df.to_json('data.json', orient='records', indent=4)
    # CSV for ML Training/Analysis
    df.to_csv('settlements.csv', index=False)
    
    print(f"Success: Generated 10,000 trades.")
    print(f"Final Market Stress Factor (Systemic): {systemic_stress:.2f}")

if __name__ == "__main__":
    generate_synthetic_data()