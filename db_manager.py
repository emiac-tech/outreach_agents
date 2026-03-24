import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(".env")

# PostgreSQL Config
DB_NAME = os.getenv("POSTGRES_DB", "outreach_db")
DB_USER = os.getenv("POSTGRES_USER", "outreach_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "outreach_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "db") # Local = localhost, Docker = db
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# ============================================================
#  🐘 POSTGRESQL SCHEMA: MASTER OUTREACH MEMORY
# ============================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS outreach_memory (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    region VARCHAR(100),
    emails TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_domain ON outreach_memory(domain);
"""

def setup_database():
    """Initializes the PostgreSQL schema and indexes."""
    print("🚦 INITIALIZING POSTGRESQL MEMORY BANK (Legacy Master Tier)...")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(SCHEMA)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ SUCCESS: Postgres Database is LIVE and Schema is ready.")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")

def migrate_txt_to_postgres(txt_file_path):
    """Retroactively syncs the .txt memory bank to the new Postgres DB."""
    if not os.path.exists(txt_file_path):
        print("ℹ️ No old .txt memory found. Starting with a fresh DB.")
        return

    print("📤 MIGRATING: TXT -> POSTGRES...")
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        
        with open(txt_file_path, 'r') as f:
            domains = [d.strip() for d in f.readlines() if d.strip()]
        
        count = 0
        for domain in domains:
            try:
                cur.execute("INSERT INTO outreach_memory (domain) VALUES (%s) ON CONFLICT DO NOTHING", (domain,))
                count += 1
            except: pass
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ MIGRATION COMPLETE: {count} historical domains moved to Postgres.")
    except Exception as e:
        print(f"❌ MIGRATION ERROR: {e}")

if __name__ == "__main__":
    setup_database()
