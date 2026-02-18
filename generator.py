import pandas as pd
import numpy as np
import json
import uuid
import random
import yfinance as yf

def get_live_vix():
    """Fetches real-time VIX to drive systemic risk."""
    try:
        # Explicitly selecting scalar to avoid FutureWarnings
        vix_df = yf.download("^VIX", period="1d", interval="1m", progress=False)
        if not vix_df.empty:
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
            
            # --- GLOBAL CALIBRATION PARAMETERS ---
            # 1. Systemic Efficiency (From DTCC SIFMA Report)
            sys_efficiency = full_seed.get("systemic_efficiency", 0.9669)
            sys_fail_baseline = max(0.0, 1.0 - sys_efficiency) # ~3.31% Baseline Risk
            
            # 2. Bond Market Context (From FINRA TRACE)
            bond_context = full_seed.get("bond_market_context", {})
            bond_liquidity_mult = bond_context.get("liquidity_multiplier", 1.0)
            bond_daily_vol_m = bond_context.get("avg_daily_volume_m", 45000.0)
            
            # 3. Ticker Universe (SEC FTD + FINRA Expanded)
            ticker_data = full_seed.get("ticker_metadata", {})
            
            if not ticker_data:
                print("Error: ticker_metadata not found in seed file.")
                return
            
            # Split tickers by class for weighted selection
            equity_tickers = [t for t, m in ticker_data.items() if m['asset_class'] == "Equity"]
            fi_tickers = [t for t, m in ticker_data.items() if m['asset_class'] != "Equity"]
            
    except Exception as e:
        print(f"File Load Error: {e}")
        return

    # 2. Setup Market Baseline
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
    print(f"📉 Systemic Base Fail Rate: {sys_fail_baseline*100:.2f}% (DTCC Baseline)")
    print(f"🏦 Bond Liquidity Context: {bond_daily_vol_m:,.0f}M Daily Vol (Multiplier: {bond_liquidity_mult}x)")

    # 4. Generation Loop
    for _ in range(num_trades):
        # Selection Logic: 70/30 split to ensure Bond visibility
        if random.random() < 0.70:
            ticker = random.choice(equity_tickers)
        else:
            ticker = random.choice(fi_tickers)
            
        asset_info = ticker_data[ticker]
        lei_id, lei_name = random.choice(leis)
        
        # --- Metadata Extraction ---
        asset_class = asset_info.get('asset_class', 'Equity')
        base_risk = asset_info.get('historical_fail_rate', 0.02)
        direction = random.choice(["DELI", "RECE"]) # DELI=Sell, RECE=Buy
        
        # --- Micro-Fluctuations (Noise) ---
        micro_jitter = np.random.uniform(-0.03, 0.03)
        trade_vol_factor = round(systemic_stress + micro_jitter, 3)

        # --- Risk Multipliers ---
        # 1. Time Stress (Peak risk at 15:00-16:00 UTC)
        hour = random.choices(range(8, 18), weights=[5,5,5,5,5,5,5,20,40,10])[0]
        prep_time = f"{hour:02d}:{random.randint(0, 59):02d}:00Z"
        time_multiplier = 4.5 if hour >= 15 else 1.0
        
        # 2. Trade Size & Volume Cap (Realism Check)
        is_fi = (asset_class != "Equity")
        
        # Log-normal distribution setup
        mu = 11.5 if is_fi else 10.2
        amt = round(np.random.lognormal(mean=mu, sigma=1.2), 2)
        
        size_multiplier = 1.0
        
        if is_fi:
            # --- NEW: Apply Bond Volume Cap ---
            # Cap single trade at 0.5% of total daily volume to prevent unrealistic trades
            # Convert millions to units: 45000 * 1,000,000 * 0.005
            max_realistic_trade = bond_daily_vol_m * 1_000_000 * 0.005
            amt = min(amt, max_realistic_trade)
            
            # Apply FINRA Liquidity Stress
            size_multiplier = bond_liquidity_mult 
            if amt > 2000000: size_multiplier *= 2.5 # Extra penalty for large blocks
        
        elif amt > 5000000:
            # Standard Equity Size Penalty
            size_multiplier = 2.0
        
        # --- Final Calculation ---
        # Total Risk = (Ticker Risk * Multipliers) + Systemic Baseline
        total_fail_prob = min((base_risk * trade_vol_factor * time_multiplier * size_multiplier) + sys_fail_baseline, 0.98)
        
        status = "PENF" if random.random() < total_fail_prob else "ACSC"
        
        reason = ""
        if status == "PENF":
            # Assign ISO reason based on direction
            if direction == "DELI":
                reason = random.choice(["INSU", "LATE"]) # Securities lack
            else:
                reason = random.choice(["CASH", "CLOS"]) # Cash lack

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
    
    print(f"✅ Success! 10,000 trades updated in data.json and settlements.csv")
    print(f"📈 Current Market Stress Factor: {systemic_stress:.2f}")

if __name__ == "__main__":
    generate_synthetic_data()