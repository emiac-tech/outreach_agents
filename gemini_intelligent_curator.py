import os
import schedule
import time
import requests
import re
import psycopg2
from google import genai
from google.genai import types
from dotenv import load_dotenv
from urllib.parse import urljoin

# ============================================================
#  💎 GEMINI INTELLIGENT AGENT - V1 (ORCHESTRATOR)
# ============================================================
load_dotenv(".env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Database Config
DB_NAME = os.getenv("POSTGRES_DB", "outreach_db")
DB_USER = os.getenv("POSTGRES_USER", "outreach_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "outreach_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
WEBHOOK_URL = "https://flow.emiactech.com/webhook/receivers-hook"

def is_domain_new(domain):
    """Check if domain is already in Postgres Memory."""
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM outreach_memory WHERE domain = %s", (domain,))
        exists = cur.fetchone()
        cur.close()
        conn.close()
        return not exists
    except Exception as e:
        print(f"⚠️ DB Check Error: {e}")
        return True # Fallback to search if DB is busy

def save_to_memory(domain, category, region, emails):
    """Insert new discovery into Postgres."""
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        cur.execute("INSERT INTO outreach_memory (domain, category, region, emails) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (domain, category, region, emails))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB Save Error: {e}")

# Internal Utilities
HEADERS = {'User-Agent': 'Mozilla/5.0'}
BAN_EMAILS = ["subscription", "feedback", "customer", "inquiry", "support"]

# 🧠 Brain Modules
from gemini_brainstormer import brainstorm_premium_domains
from gemini_critic import ai_quality_critic

def extract_emails_smart(html_text, domain):
    mails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-]+\.[a-z]{2,5}", html_text.lower()))
    # Prefix Filter
    filtered = [m for m in mails if not any(b in m.split('@')[0].lower() for b in BAN_EMAILS)]
    # Domain & relevance filter
    valid = [m for m in filtered if domain in m or any(x in m for x in ["gmail.com", "outlook.com", "yahoo.com"])]
    return "\n".join(list(set(valid))[:5]) if valid else "No Email Found"

def run_curator_session(niche, region, target_count=10):
    print(f"\n🚀 Starting Intelligent Curation Session: [{niche}] in [{region}]")
    
    # 1. AI BRAINSTORMING (Gemini)
    print("🧠 AI Brainstorming premium domains...")
    raw_domains = brainstorm_premium_domains(niche, region, count=target_count*2)
    if not raw_domains: return
    
    found_in_session = 0
    for item in raw_domains:
        if found_in_session >= target_count: break
        
        domain = item['domain'].lower().replace("www.", "").strip()
        reason = item['reason']
        
        # 2. SQL SEARCH (Zero-Duplication Guard)
        if not is_domain_new(domain):
            print(f"   ❌ Rejected: Already in Postgres Memory.")
            continue
            
        print(f"🧐 AI Auditor Checking: {domain}...")
        verdict = ai_quality_critic(domain, reason)
        
        if verdict['verdict'] == "REJECT":
            print(f"   ❌ Rejected: {verdict['reason']}")
            continue
            
        # 3. VERIFICATION & EXTRACTION
        print(f"   ✅ PASS: {domain}. Verifying live...")
        try:
            r = requests.get(f"https://www.{domain}", headers=HEADERS, timeout=12, verify=False)
            if r.status_code == 200:
                emails = extract_emails_smart(r.text, domain)
                
                # 4. SEND TO WEBHOOK (Primary Delivery)
                payload = {
                    "Domain (www)": f"www.{domain}",
                    "Category": niche,
                    "URL": f"https://www.{domain}",
                    "Extracted Mails": emails,
                    "Region": region
                }
                # (Webhook injection logic remains same)
                try: 
                    requests.post(WEBHOOK_URL, json=payload, timeout=8)
                    print("   📡 WEBHOOK INJECTED SUCCESSFUL.")
                except: print("   ⚠️ Webhook failed.")
                
                # 5. ENTERPRISE SAVE: Postgres + Webhook
                save_to_memory(domain, niche, region, emails)
                
                found_in_session += 1
                print(f"   🏆 SUCCESSFULLY ADDED: {domain} ({found_in_session}/{target_count})")
            else:
                print(f"   ⚠️ Site error ({r.status_code}). Skipping...")
        except Exception as e:
            print(f"   ⚠️ Connection error. Skipping...")
            
    print(f"\n✅ Session Finished. Added {found_in_session} PREMIUM sites to your sheet.")

# ============================================================
#  🚦 SCHEDULER: AUTONOMOUS 24/7 OPERATION
# ============================================================

def job():
    print(f"\n--- 🏁 DAILY RUN STARTING [Daily Goal: 300 Sites] ---")
    
    # 300 sites spread across 5 regions to guarantee variety
    regions = ["UAE (Premium)", "Saudi Arabia (KSA)", "Egypt", "Qatar & Kuwait", "Jordan & Levant"]
    niche = "Premium Business, Editorials & PR Agencies"
    
    # Target 60 sites per region to reach 300 total
    for region in regions:
        print(f"\n🌍 Starting Enrichment Batch for: {region}")
        run_curator_session(niche, region, target_count=60)
        
    print(f"\n--- ✅ 300-SITE DAILY RUN COMPLETE. RESUMING STANDBY. ---")

if __name__ == "__main__":
    print("🚀 INTELLIGENT AGENT V1: AUTONOMOUS PRODUCTION MODE.")
    print("⏰ Daily Timer: 09:00 AM.")
    print("🎯 Daily Target: 300 NEW Premium Sites.")
    
    # 1. Schedule Daily at 09:00
    schedule.every().day.at("09:00").do(job)
    
    # 2. Start the 24/7 Daemon
    print("🟢 Standby Mode Active. Monitoring timer...")
    while True:
        schedule.run_pending()
        time.sleep(60)
