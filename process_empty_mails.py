import os
import requests
import gspread
import time
import re
from google import genai
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup

# ============================================================
#  🚀 AUTOMATED BULK ENRICHMENT: EMPTY MAILS TAB
# ============================================================

load_dotenv("/Users/sakshiagarwal/Desktop/Extracting Mails/.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# IDs & Config
SERVICE_ACCOUNT_FILE = "/Users/sakshiagarwal/Downloads/high-apricot-409308-6ebb2217d023.json"
GOOGLE_SHEET_ID      = "1H-2TBmVdoWwuHaxU671h0_gpkLApWEBdp789HITC7hQ"
WEBHOOK_URL          = "https://flow.emiactech.com/webhook/receivers-hook"

def get_region_from_ai(domain):
    """Uses Gemini to identify the country/region of a domain."""
    try:
        prompt = f"In which specific country or region is the website '{domain}' based? Give only the country name."
        response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
        return response.text.strip().replace('\n', '')
    except: return "MENA (Uncertain)"

def extract_emails_smart(html, domain):
    """Clean email extraction ignoring generic boxes."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    found = re.findall(email_pattern, html)
    
    # Filtering rules
    blacklist = ['subscription', 'support', 'help', 'no-reply', 'feedback', 'customer', 'noreply', 'inquiry', 'sales', 'billing']
    valid_emails = []
    
    for email in set(found):
        email_lower = email.lower()
        if any(word in email_lower for word in blacklist): continue
        if domain.lower() in email_lower.split('@')[1]: # Check domain match
            valid_emails.append(email_lower)
            
    return ", ".join(valid_emails) if valid_emails else "No Premium Email Found"

def process_enrichment():
    print("🚦 STARTING BULK ENRICHMENT: Extraction + Region ID...")
    
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    ws = sh.worksheet("Empty Mails")
    
    rows = ws.get_all_values()
    # Header: ['Domain', 'Category', 'Region', 'URL', 'Extracted Mails']
    
    batch = []  # 🗂️ Collect all payloads before sending

    for i in range(1, len(rows)): # Skip header
        row = rows[i]
        domain_raw = row[0]
        category = row[1]
        url = row[3]
        
        # Clean domain
        domain = domain_raw.replace("www.", "").replace("https://", "").replace("http://", "").split("/")[0]
        
        print(f"🔍 [{i}/{len(rows)-1}] Processing: {domain}...")
        
        # 1. Identify Region
        region = get_region_from_ai(domain)
        
        # 2. Extract Emails
        emails = "No Email Found"
        try:
            r = requests.get(url, timeout=12, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                emails = extract_emails_smart(r.text, domain)
        except: emails = "No Email Found (Timeout)"
        
        # 3. Update GSheet (Col C and Col E) - Col indices are 1-based (C=3, E=5)
        ws.update_cell(i+1, 3, region) # Region
        ws.update_cell(i+1, 5, emails) # Emails
        
        # 4. Add to batch (no webhook call yet)
        batch.append({
            "Domain (www)": domain_raw,
            "Category": category,
            "URL": url,
            "Extracted Mails": emails,
            "Region": region,
            "Enrichment Source": "Gemini-Enrich"
        })
        print(f"   📦 Queued: {region} | {emails}")

    # 5. Send all enriched sites in ONE webhook request
    if batch:
        try:
            r = requests.post(WEBHOOK_URL, json={"sites": batch, "total": len(batch)}, timeout=60)
            if r.status_code == 200:
                print(f"\n📡 WEBHOOK BATCH SENT: {len(batch)} enriched sites in one request.")
            else:
                print(f"\n⚠️ Webhook batch failed (Error {r.status_code}).")
        except Exception as e:
            print(f"\n❌ Webhook batch request error: {e}")
    
    print("\n🏆 PROJECT COMPLETE. ALL MAILS ENRICHED AND REGIONS IDENTIFIED.")

if __name__ == "__main__":
    process_enrichment()
