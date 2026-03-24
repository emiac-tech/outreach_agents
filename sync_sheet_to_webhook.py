import os
import requests
import gspread
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
        
        batch = []  # 🗂️ Collect all payloads first
        for row in data_rows:
            # Map common row structure [Domain, Category, URL, Mails, Region]
            if len(row) < 5: continue
            
            batch.append({
                "Domain (www)": row[0],
                "Category": row[1],
                "URL": row[2],
                "Extracted Mails": row[3],
                "Region": row[4]
            })

        # 2. Send ALL sites in ONE request
        if batch:
            try:
                r = requests.post(WEBHOOK_URL, json={"sites": batch, "total": len(batch)}, timeout=60)
                if r.status_code == 200:
                    print(f"\n🏆 SYNC COMPLETE! All {len(batch)} sites sent in one webhook request.")
                else:
                    print(f"\n⚠️ Webhook returned error {r.status_code}.")
            except Exception as e:
                print(f"\n❌ Webhook request failed: {e}")
        else:
            print("\n⚠️ No data rows found to sync.")
        
    except Exception as e:
        print(f"❌ Critical Sync Error: {e}")

if __name__ == "__main__":
    sync_all_data()
