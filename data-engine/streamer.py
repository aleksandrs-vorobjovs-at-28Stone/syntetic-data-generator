import requests
import time
import sys

# ==========================================
# ⚙️ CONFIGURATION (Update these URLs!)
# ==========================================
# 1. Your new GitHub Pages CDN URL "https://<account>.github.io/<repo>/data-engine/data.json"
DATA_URL = "https://aleksandrs-vorobjovs-at-28stone.github.io/syntetic-data-generator/data-engine/data.json" 

# 2. Developer 5's n8n Webhook URL (You will get this when n8n is set up)
#N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/settlement-risk"
# temporarily point it to a free testing site like https://webhook.site/ just to watch it successfully post data over the internet!
N8N_WEBHOOK_URL = "https://webhook.site/20cb31dc-9953-4ce2-ac98-c8abcc484875"

# 3. Pacing (Crucial: 2 seconds prevents HTTP 429 Too Many Requests errors)
PACE_SECONDS = 2 
# ==========================================

def fetch_trades():
    print(f"📥 Fetching live trade batch from: {DATA_URL}")
    try:
        response = requests.get(DATA_URL)
        response.raise_for_status() # Throws an error for 404s, etc.
        trades = response.json()
        print(f"✅ Successfully loaded {len(trades)} trades into memory.\n")
        return trades
    except Exception as e:
        print(f"❌ Failed to fetch data. Check your DATA_URL. Error: {e}")
        sys.exit(1)

def stream_trades(trades):
    total_trades = len(trades)
    print("⏳ Beginning real-time streaming sequence...")
    print("🛑 Press Ctrl+C to stop the stream at any time.\n")
    print("-" * 50)

    try:
        for index, trade in enumerate(trades, start=1):
            
            # --- 1. MASKING (Data Sanitization) ---
            # We pop the answers out of the dictionary.
            # We save them in variables just so we can print them locally for debugging!
            actual_status = trade.pop("Status", "UNKNOWN")
            actual_reason = trade.pop("ISO_ReasonCode", "NONE")

            # --- 2. SENDING (The Egress) ---
            print(f"[{index}/{total_trades}] 🚀 Sending Trade {trade.get('UETR')}...")
            
            try:
                # We send the sanitized 'trade' dictionary as the JSON payload
                response = requests.post(N8N_WEBHOOK_URL, json=trade)
                
                # Check for ANY successful 2xx status code (200, 201, 202, etc.)
                if response.ok:
                    print(f"   ✅ n8n accepted (Hidden truth: {actual_status} - {actual_reason})")
                else:
                    print(f"   ⚠️ n8n responded with HTTP {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Network error hitting n8n webhook: {e}")

            # --- 3. PACING (The Rate Limiter) ---
            time.sleep(PACE_SECONDS)

    except KeyboardInterrupt:
        print("\n\n🛑 Stream paused manually by user. Goodbye!")

if __name__ == "__main__":
    # 1. Pull the data
    batch = fetch_trades()
    
    # 2. Start the infinite drip
    stream_trades(batch)