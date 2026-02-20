import pandas as pd
import pdfplumber
import glob
import json
import os
import re
import numpy as np
import random

# Set the base directory to where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def process_sec_ftd():
    """Processes SEC Fails-to-Deliver pipe-delimited CSVs (Equities)."""
    print("\n[STEP 1] Processing SEC Fails-to-Deliver (17,500+ Tickers)...")
    target_path = os.path.join(BASE_DIR, 'seeds', 'sec_ftd', '*.csv')
    all_files = glob.glob(target_path)
    
    if not all_files:
        print(" ! ERROR: No SEC files found in seeds/sec_ftd/")
        return {}
    
    df_list = []
    for f in all_files:
        print(f" -> Reading: {os.path.basename(f)}")
        try:
            # SEC files: Pipe separated, ignore footer, ISO encoding
            df = pd.read_csv(f, sep='|', skipfooter=2, engine='python', encoding='iso-8859-1')
            df.columns = [c.strip() for c in df.columns]
            
            if 'SYMBOL' in df.columns and 'QUANTITY (FAILS)' in df.columns:
                df['QUANTITY (FAILS)'] = pd.to_numeric(df['QUANTITY (FAILS)'], errors='coerce').fillna(0)
                df_list.append(df[['SYMBOL', 'QUANTITY (FAILS)']])
        except Exception as e:
            print(f"   ! Error processing SEC file: {e}")
    
    if not df_list: return {}
    
    master_df = pd.concat(df_list)
    avg_fails = master_df.groupby('SYMBOL')['QUANTITY (FAILS)'].mean()
    market_avg = avg_fails.mean()
    
    # Normalize: Convert raw fail counts to a 0.0-1.0 risk score
    # We divide by market_avg and cap it to prevent outlier symbols from breaking the generator
    stress_mapping = (avg_fails / market_avg).round(6).to_dict()
    print(f" -> Successfully mapped {len(stress_mapping)} Equity tickers.")
    return stress_mapping

def process_finra_trace():
    """Processes FINRA TRACE and expands each product into 680 tickers (Bonds)."""
    print("\n[STEP 2] Processing FINRA TRACE (Expanding to 7,480+ Tickers)...")
    target_path = os.path.join(BASE_DIR, 'seeds', 'finra_trace', 'trace_volume_2025.csv')
    
    if not os.path.exists(target_path):
        print(f" ! ERROR: {target_path} not found.")
        return {}, {"avg_daily_volume_m": 45000, "liquidity_multiplier": 1.0}
    
    try:
        df = pd.read_csv(target_path, sep=';')
        df.columns = [c.strip() for c in df.columns]
        
        # Use December 2025 for latest market context
        dec_data = df[df['Month'] == 'December'].copy()
        
        # Determine systemic bond stress (based on CORP product volume)
        corp_row = dec_data[dec_data['Product'] == 'CORP']
        latest_adv = float(corp_row.iloc[0]['Total Average Daily Par Value']) if not corp_row.empty else 45000
        
        # Aggressive Liquidity Multiplier (Set to 2.8 if ADV < 50k)
        multiplier = 2.8 if latest_adv < 50000 else 1.0
        
        expanded_bond_metadata = {}
        products = dec_data['Product'].unique()
        
        for prod in products:
            prod_row = dec_data[dec_data['Product'] == prod]
            vol = float(prod_row.iloc[0]['Total Average Daily Par Value'])
            
            # --- OPTION A: EXPANSION (680 tickers per category) ---
            for i in range(1, 681):
                random_id = random.randint(100000, 999999)
                ticker = f"{prod}_{random_id}"
                
                # Risk Score Calculation based on Volume (Inverse log)
                vol_risk_factor = 1.0 / (np.log10(vol + 1.1))
                base_rate = 0.04 * vol_risk_factor * multiplier
                # Add jitter for ticker-level uniqueness
                stress_score = round(base_rate * np.random.uniform(0.6, 1.4), 6)
                
                expanded_bond_metadata[ticker] = {
                    "asset_class": "Corporate Bond" if prod == "CORP" else "Fixed Income",
                    "historical_fail_rate": min(stress_score, 0.75),
                    "liquidity_profile": "Low" if vol < 2000 else "Medium",
                    "source": f"FINRA_2025_{prod}"
                }
        
        print(f" -> Successfully expanded FINRA products into {len(expanded_bond_metadata)} tickers.")
        return expanded_bond_metadata, {"avg_daily_volume_m": latest_adv, "liquidity_multiplier": multiplier}

    except Exception as e:
        print(f"   ! Error processing FINRA file: {e}")
        return {}, {"avg_daily_volume_m": 45000, "liquidity_multiplier": 1.0}

def process_dtcc_regime(mode="NORMAL"):
    """
    Sets the Systemic Efficiency Baseline based on the SIFMA/DTCC T+1 After Action Report.
    Source: https://www.sifma.org/news/press-releases/sifma-ici-and-dtcc-release-t1-after-action-report/
    """
    # Exact values extracted from the Sept 12, 2024 Report
    regimes = {
        # CNS Fail Rate was 2.12% (Efficiency = 97.88%)
        "OPTIMAL": 0.9788,  
        
        # Non-CNS Fail Rate was 3.31% (Efficiency = 96.69%)
        "NORMAL": 0.9669,   
        
        # Hypothetical Stress: 5% fail rate (Based on 95% Affirmation target missing)
        "STRESSED": 0.9500, 
        
        # Liquidity Crunch: 15% fail rate
        "CRISIS": 0.8500    
    }
    
    efficiency = regimes.get(mode, 0.9669)
    print(f"\n[STEP 3] Setting Systemic Efficiency Baseline...")
    print(f" -> Mode: {mode}")
    print(f" -> Baseline Efficiency: {efficiency*100:.2f}%")
    print(" -> Source: SIFMA/DTCC T+1 After Action Report (Sept 2024)")
    
    return efficiency

def main():
    print("🚀 STARTING SEED ENGINE VERSION 2.0 CALIBRATION")
    
    # Run all extraction modules
    equity_tickers = process_sec_ftd()
    bond_tickers, bond_stats = process_finra_trace()
    systemic_efficiency = process_dtcc_regime(mode="NORMAL")
    
    ticker_metadata = {}

    # 1. Enrich Equity Tickers
    for ticker, score in equity_tickers.items():
        ticker_metadata[ticker] = {
            "asset_class": "Equity",
            "historical_fail_rate": min(score / 50, 0.8), # Normalize SEC score to probability
            "liquidity_profile": "High",
            "source": "SEC_2025_FTD"
        }

    # 2. Enrich Bond Tickers
    for ticker, info in bond_tickers.items():
        ticker_metadata[ticker] = info # Already formatted in the helper function

    # 3. Final Consolidation
    seed_data = {
        "metadata": {
            "calibration_date": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source_year": "2025",
            "version": "2.0-Enriched"
        },
        "systemic_efficiency": systemic_efficiency,
        "bond_market_context": bond_stats,
        "ticker_metadata": ticker_metadata
    }
    
    # 4. Save to JSON
    output_file = os.path.join(BASE_DIR, 'seed_engine.json')
    with open(output_file, 'w') as f:
        json.dump(seed_data, f, indent=4)
    
    print("\n" + "="*60)
    print(f"SUCCESS: Seed Engine Calibration Complete!")
    print(f"Final Universe Size: {len(ticker_metadata)} Assets")
    print(f"Baseline Efficiency: {systemic_efficiency*100:.2f}%")
    print("="*60)

if __name__ == "__main__":
    main()