import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load Environment and Configure Gemini
load_dotenv("/Users/sakshiagarwal/Desktop/Extracting Mails/.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MEMORY_FILE = "/Users/sakshiagarwal/Desktop/Extracting Mails/master_scraped_domains.txt"

def load_memory():
    if not os.path.exists(MEMORY_FILE): return set()
    with open(MEMORY_FILE, 'r') as f:
        return {line.strip().lower() for line in f if line.strip()}

def is_duplicate(domain):
    mem = load_memory()
    return domain.lower().replace("www.", "") in mem

def ai_quality_critic(domain, site_sample_text):
    """
    Acts as the 'Human-Like Judge' to determine if a site is PR-grade or Link-Farm.
    """
    # 1. Quick Duplicate Check (Saves API Costs)
    if is_duplicate(domain):
        return {"verdict": "REJECT", "reason": "Already in Master Memory Bank."}
    
    # 2. AI Intelligence Check
    prompt = f"""
    You are a professional SEO Quality Auditor.
    Task: Critically evaluate this website: {domain}
    Summary / Metadata provided: {site_sample_text}
    
    Criteria for 'PREMIUM' (PASS):
    - Original editorial content (News, Industry Analysis, Magazine).
    - Established national/regional brand.
    - No obvious 'Sell Links Here' or 'Guest Post for $10' flags on homepage.
    
    Criteria for 'LINK FARM' (REJECT):
    - Sites that exist only to sell guest posts.
    - Promotional directories masquerading as news.
    - General blogs with no specific niche.
    
    Output Format:
    Return ONLY a JSON object:
    {{"verdict": "PASS" or "REJECT", "reason": "1 short sentence explaining why."}}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        
        raw_text = response.text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        print(f"⚠️ Error during AI Quality Check: {e}")
        return {"verdict": "REJECT", "reason": "AI Error"}

if __name__ == "__main__":
    # Test Run
    print("🧐 Testing AI Quality Critic on 'zawya.com'...")
    verdict = ai_quality_critic("zawya.com", "Leading MENA business and financial news platform.")
    print(f"Result: {verdict['verdict']} - {verdict['reason']}")
    
    print("\n🧐 Testing AI Quality Critic on 'linksformarketing.blogspot.com'...")
    verdict = ai_quality_critic("linksformarketing.blogspot.com", "Post any link here for $5, universal guest posting site.")
    print(f"Result: {verdict['verdict']} - {verdict['reason']}")
