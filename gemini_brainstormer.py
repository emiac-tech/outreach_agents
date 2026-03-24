import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load Environment and Configure Gemini
load_dotenv(".env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def brainstorm_premium_domains(niche, region, count=20):
    """
    Uses Gemini's Internal Knowledge (No Grounding to avoid 429)
    """
    prompt = f"""
    Search your internal expert database for {count} HIGH-AUTHORITY, PREMIUM news and business publishers specifically for the region: {region}.
    Niche focus: {niche}.
    
    Output Format:
    Return ONLY a JSON list of objects. Each object must have:
    - "domain": strictly the domain (e.g., 'example.com')
    - "reason": 1 sentence why it is high quality.
    
    Example: [{{"domain": "zawya.com", "reason": "Leading business news provider in MENA."}}]
    """
    
    try:
        # NO GROUNDING FOR NOW (Avoiding 429)
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        
        # Clean the response to extract JSON
        raw_text = response.text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"❌ Error during AI Brainstorming: {e}")
        return []

if __name__ == "__main__":
    # Test Run
    print("🧠 AI Brainstorming (Internal Knowledge Mode)...")
    results = brainstorm_premium_domains("Real Estate & Economy", "UAE", count=5)
    if results:
        print(f"✅ Success! Found {len(results)} premium domains.")
        for idx, item in enumerate(results):
            print(f"{idx+1}. {item['domain']} - {item['reason']}")
    else:
        print("⚠️ No results returned from AI.")
