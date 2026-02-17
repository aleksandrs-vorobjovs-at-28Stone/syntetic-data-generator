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
        vix = yf.download("^VIX", period="1d", interval="1m")['Close'].iloc[-1]
        return round(float(vix), 2)
    except:
        return 16.50 # Realistic default for 2026 baseline

def generate_synthetic_data(num_trades=10000):
    # 1. Load Seed Data
    try:
        with open('seed_engine.json', 'r') as f:
            seed_data = json.load(f)
    except FileNotFoundError:
        print("Error: seed_engine.json not found. Please run calibration first.")
        return

    # 2. Setup Market Baseline (VIX)
    current_vix = get_live_vix()
    vix_baseline = 15.0
    systemic_stress = current_vix / vix_baseline

    # 3. Reference Data
    leis = [
        ("2138006M8651", "JPM_CHASE_NA"),
        ("5493001KJX12", "GOLDMAN_SACHS_INTL"),
        ("7LR9S95S8L34", "NOMURA_INTL"),
        ("549300675865", "BARCLAYS_CAPITAL"),
        ("213800VZW961", "BEYOND_ALPHA_HF")
    ]

    trades = []
    
    # 4. Generation Loop
    for _ in range(num_trades):
        asset = random.choice(seed_data)
        lei_id, lei_name = random.choice(leis)
        
        # --- Injecting Micro-Fluctuations (Noise) ---
        # We add a random "jitter" per trade to avoid identical volatility values
        micro_jitter = np.random.uniform(-0.04, 0.04)
        trade_vol_factor = round(systemic_stress + micro_jitter, 3)

        # --- Probability of Failure Calculation ---
        # Base risk from SEC/FINRA seeds
        base_risk = asset['historical_fail_rate']
        
        # Factor A: Time Stress (Late trades fail 4x more)
        # Randomly generate a time (HH:MM)
        hour = random.choices(range(8, 18), weights=[5,5,5,5,5,5,10,20,40,10])[0]
        minute = random.randint(0, 59)
        prep_time = f"{hour:02d}:{minute:02d}:00Z"
        
        time_multiplier = 4.0 if hour >= 15 else 1.0
        
        # Factor B: Trade Size (Large trades have liquidity risk)
        # Log-normal distribution: most are small, some are huge
        amt = round(np.random.lognormal(mean=10, sigma=1.5), 2)
        size_multiplier = 2.5 if amt > 5000000 else 1.0
        
        # Final Failure Probability
        fail_prob = base_risk * trade_vol_factor * time_multiplier * size_multiplier
        
        # Determine Status (ACSC = Success, PENF = Fail)
        status = "PENF" if random.random() < fail_prob else "ACSC"
        
        # Assign Reason Code if failed
        reason = ""
        if status == "PENF":
            reason = random.choice(["INSU", "LATE", "CASH", "CLOS"])

        # 5. Build Record
        trades.append({
            "UETR": str(uuid.uuid4()),
            "InstructingParty_LEI": lei_id,
            "Counterparty": lei_name,
            "Asset_ISIN": asset['ticker'],
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
    
    # JSON for Dashboard
    df.to_json('data.json', orient='records', indent=4)
    # CSV for ML Training
    df.to_csv('settlements.csv', index=False)
    
    print(f"Generation complete: 10,000 trades generated.")
    print(f"Market Stress Baseline: {systemic_stress:.2f}")

if __name__ == "__main__":
    generate_synthetic_data()