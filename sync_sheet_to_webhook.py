import os
import requests
import gspread
import time
from google.oauth2.service_account import Credentials

# Configuration
SERVICE_ACCOUNT_FILE = "/Users/sakshiagarwal/Downloads/high-apricot-409308-6ebb2217d023.json"
GOOGLE_SHEET_ID      = "1H-2TBmVdoWwuHaxU671h0_gpkLApWEBdp789HITC7hQ"
WEBHOOK_URL          = "https://flow.emiactech.com/webhook/receivers-hook"

def sync_all_data():
    print("📡 INITIALIZING RETROACTIVE SYNC: Sheet -> Webhook...")
    
    # 1. Access Google Sheet
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        ws = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).worksheet("Combined Data")
        all_rows = ws.get_all_values()
        
        # Skip header (assuming 1st row is header)
        data_rows = all_rows[1:]
        print(f"📦 Found {len(data_rows)} sites in your Master Sheet.")
        
        count = 0
        for row in data_rows:
            # Map common row structure [Domain, Category, URL, Mails, Region]
            if len(row) < 5: continue
            
            payload = {
                "Domain (www)": row[0],
                "Category": row[1],
                "URL": row[2],
                "Extracted Mails": row[3],
                "Region": row[4]
            }
            
            # Send to Webhook
            try:
                r = requests.post(WEBHOOK_URL, json=payload, timeout=8)
                if r.status_code == 200:
                    count += 1
                    print(f"👉 [{count}/{len(data_rows)}] SYNCED: {row[0]}")
                else:
                    print(f"⚠️ Failed to sync {row[0]} (Error {r.status_code})")
            except Exception as e:
                print(f"⚠️ Connection error for {row[0]}")
            
            # Small delay to prevent webhook flooding
            time.sleep(0.1)

        print(f"\n🏆 SYNC COMPLETE! All {count} Master Sites are now on your Webhook.")
        
    except Exception as e:
        print(f"❌ Critical Sync Error: {e}")

if __name__ == "__main__":
    sync_all_data()
