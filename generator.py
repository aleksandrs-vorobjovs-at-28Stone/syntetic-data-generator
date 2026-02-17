import pandas as pd
import numpy as np
import json
import uuid
import random
import yfinance as yf

def get_live_vix():
    """Fetches real-time VIX baseline or uses a default if API fails."""
    try:
        vix_df = yf.download("^VIX", period="1d", interval="1m", progress=False)
        if not vix_df.empty:
            # Explicitly select scalar to avoid FutureWarnings
            vix_value = vix_df['Close'].values[-1]
            return round(float(vix_value), 2)
        return 16.50
    except:
        return 16.50 

def generate_synthetic_data(num_trades=10000):
    # 1. Load the Enriched Seed Engine
    try:
        with open('seed_engine.json', 'r') as f:
            full_seed = json.load(f)
            ticker_data = full_seed.get("ticker_metadata", {})
            
            if not ticker_data:
                print("Error: ticker_metadata not found in seed file.")
                return
            
            # Categorize tickers for balanced selection
            equity_tickers = [t for t, m in ticker_data.items() if m['asset_class'] == "Equity"]
            # This captures both "Corporate Bond" and "Fixed Income"
            fi_tickers = [t for t, m in ticker_data.items() if m['asset_class'] != "Equity"]
            
    except Exception as e:
        print(f"File Load Error: {e}")
        return

    # 2. Setup Market Baseline (Systemic Stress)
    current_vix = get_live_vix()
    vix_baseline = 15.0
    systemic_stress = current_vix / vix_baseline

    # 3. Institutional Counterparties (LEIs)
    leis = [
        ("2138006M8651", "JPM_CHASE_NA"),
        ("5493001KJX12", "GOLDMAN_SACHS_INTL"),
        ("7LR9S95S8L34", "NOMURA_INTL"),
        ("549300675865", "BARCLAYS_CAPITAL"),
        ("213800VZW961", "BEYOND_ALPHA_HF")
    ]

    trades = []
    print(f"🚀 Generating {num_trades} trades...")
    print(f"📊 Market Universe: {len(equity_tickers)} Equities, {len(fi_tickers)} Fixed Income/Bonds.")

    # 4. Generation Loop
    for _ in range(num_trades):
        # 70/30 split logic as requested
        if random.random() < 0.70:
            ticker = random.choice(equity_tickers)
        else:
            ticker = random.choice(fi_tickers)
            
        asset_info = ticker_data[ticker]
        lei_id, lei_name = random.choice(leis)
        
        # --- Metadata Extraction ---
        asset_class = asset_info.get('asset_class', 'Equity')
        base_risk = asset_info.get('historical_fail_rate', 0.02)
        direction = random.choice(["DELI", "RECE"]) # DELI=Sell/Deliver, RECE=Buy/Receive
        
        # --- Micro-Fluctuations (Noise) ---
        micro_jitter = np.random.uniform(-0.03, 0.03)
        trade_vol_factor = round(systemic_stress + micro_jitter, 3)

        # --- Risk Multipliers ---
        # 1. Time Stress (Operational risk increases toward market close)
        hour = random.choices(range(8, 18), weights=[5,5,5,5,5,5,5,20,40,10])[0]
        prep_time = f"{hour:02d}:{random.randint(0, 59):02d}:00Z"
        time_multiplier = 4.5 if hour >= 15 else 1.0
        
        # 2. Trade Size (Institutional realism)
        # Fixed Income trades are typically larger than Equity trades
        is_fi = (asset_class != "Equity")
        mu = 11.5 if is_fi else 10.2
        amt = round(np.random.lognormal(mean=mu, sigma=1.2), 2)
        
        # Size risk: Bonds/FI trades have a lower liquidity ceiling
        if is_fi and amt > 2000000:
            size_multiplier = 3.5
        elif not is_fi and amt > 5000000:
            size_multiplier = 2.0
        else:
            size_multiplier = 1.0
        
        # --- Final Calculation ---
        # Probability calculation capped at 98%
        fail_prob = min(base_risk * trade_vol_factor * time_multiplier * size_multiplier, 0.98)
        status = "PENF" if random.random() < fail_prob else "ACSC"
        
        reason = ""
        if status == "PENF":
            # Context-aware ISO 20022 reason codes
            if direction == "DELI":
                reason = random.choice(["INSU", "LATE"]) # Securities lack
            else:
                reason = random.choice(["CASH", "CLOS"]) # Cash/Funding lack

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

    # 6. Export Results
    df = pd.DataFrame(trades)
    df.to_json('data.json', orient='records', indent=4)
    df.to_csv('settlements.csv', index=False)
    
    print(f"✅ Success! 10,000 trades generated.")
    print(f"📈 Systemic Stress Level: {systemic_stress:.2f}")

if __name__ == "__main__":
    generate_synthetic_data()