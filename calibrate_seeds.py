import pandas as pd
import pdfplumber
import glob
import json
import os
import re

# Set the base directory to where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def process_sec_ftd():
    """Processes SEC Fails-to-Deliver pipe-delimited CSVs."""
    print("\n[STEP 1] Processing SEC Fails-to-Deliver (Pipe Delimited)...")
    target_path = os.path.join(BASE_DIR, 'seeds', 'sec_ftd', '*.csv')
    all_files = glob.glob(target_path)
    
    if not all_files:
        print(" ! ERROR: No SEC files found in seeds/sec_ftd/")
        return {}
    
    df_list = []
    for f in all_files:
        print(f" -> Found: {os.path.basename(f)}")
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
    
    # Normalize risk: 1.0 is average.
    stress_mapping = (avg_fails / market_avg).round(2).to_dict()
    print(f" -> Successfully mapped {len(stress_mapping)} tickers.")
    return stress_mapping

def process_finra_trace():
    """Processes FINRA TRACE semicolon-delimited CSVs."""
    print("\n[STEP 2] Processing FINRA TRACE (Semicolon Delimited)...")
    target_path = os.path.join(BASE_DIR, 'seeds', 'finra_trace', '*.csv')
    files = glob.glob(target_path)
    
    if not files:
        print(" ! SKIP: No FINRA files found in seeds/finra_trace/")
        return {"avg_daily_volume_m": 30000, "liquidity_multiplier": 1.0}
    
    f = files[0]
    print(f" -> Found: {os.path.basename(f)}")
    
    try:
        # FINRA logic: Semicolon separator based on your raw data
        df = pd.read_csv(f, sep=';')
        df.columns = [c.strip() for c in df.columns]
        
        # Filter for 'CORP' (Corporate Bonds)
        corp_rows = df[df['Product'] == 'CORP']
        
        if corp_rows.empty:
            print("   ! Error: 'CORP' product not found in the CSV.")
            return {"avg_daily_volume_m": 30000, "liquidity_multiplier": 1.0}
            
        # Get the first row (most recent month: Dec 2025)
        latest_adv = float(corp_rows.iloc[0]['Total Average Daily Par Value'])
        
        # Aggressive Liquidity Multiplier
        # Based on your data (~45k-60k range), we stress if it dips below 50k
        multiplier = 1.0
        if latest_adv < 45000: multiplier = 2.8 
        elif latest_adv < 50000: multiplier = 1.6 
        
        print(f" -> Latest Corp ADV: ${latest_adv}M (Multiplier: {multiplier})")
        return {"avg_daily_volume_m": latest_adv, "liquidity_multiplier": multiplier}

    except Exception as e:
        print(f"   ! Error processing FINRA file: {e}")
        return {"avg_daily_volume_m": 30000, "liquidity_multiplier": 1.0}

def process_dtcc_pdfs():
    """Extracts settlement percentages from DTCC PDFs."""
    print("\n[STEP 3] Processing DTCC Reports (PDF)...")
    target_path = os.path.join(BASE_DIR, 'seeds', 'dtcc_reports', '*.pdf')
    files = glob.glob(target_path)
    
    if not files:
        print(" ! SKIP: No DTCC PDFs found in seeds/dtcc_reports/")
        return 0.985
    
    efficiencies = []
    for f in files:
        print(f" -> Found: {os.path.basename(f)}")
        try:
            with pdfplumber.open(f) as pdf:
                text = " ".join([p.extract_text() or "" for p in pdf.pages])
                # Find percentages like 98.5%
                matches = re.findall(r'(\d{2}\.\d+)%', text)
                if matches:
                    efficiencies.append(float(max(matches)) / 100)
        except Exception as e:
            print(f"   ! Error parsing PDF {os.path.basename(f)}: {e}")
            
    return sum(efficiencies) / len(efficiencies) if efficiencies else 0.985

def main():
    print("Starting Seed Engine Calibration...")
    
    # Run all modules
    systemic_efficiency = process_dtcc_pdfs()
    bond_market = process_finra_trace()
    ticker_stress = process_sec_ftd()
    
    # Consolidate into the brain file
    seed_data = {
        "metadata": {
            "calibration_date": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source_year": "2025",
            "aggression_level": "High"
        },
        "systemic_efficiency": systemic_efficiency,
        "bond_market": bond_market,
        "ticker_stress_scores": ticker_stress
    }
    
    # Save the JSON
    output_file = os.path.join(BASE_DIR, 'seed_engine.json')
    with open(output_file, 'w') as f:
        json.dump(seed_data, f, indent=4)
    
    print("\n" + "="*50)
    print(f"SUCCESS: Seed Engine Calibration Complete!")
    print(f"Output: {output_file}")
    print(f"Stats: {len(ticker_stress)} tickers, {systemic_efficiency*100}% baseline.")
    print("="*50)

if __name__ == "__main__":
    main()