import os
import time
import requests
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Import our Brain modules
from gemini_intelligent_curator import run_curator_session
from google import genai

# ============================================================
#  🚀 INTELLIGENT AGENT: API SERVER (FOR N8N / PRODUCTION)
# ============================================================

app = Flask(__name__)
CORS(app)
load_dotenv(".env")

# Memory State
AGENT_STATUS = "Standby"
LAST_RUN_LOG = "Ready for deployment."

def daily_task_wrapper():
    """Background thread to run the 300-site curation."""
    global AGENT_STATUS, LAST_RUN_LOG
    AGENT_STATUS = "Running (300-Site Goal)"
    
    try:
        print("\n🏁 API TRIGGER RECEIVED: Starting 300-Site Batch...")
        regions = ["UAE (Premium)", "Saudi Arabia (KSA)", "Egypt", "Qatar & Kuwait", "Jordan & Levant"]
        niche = "Premium Business, Editorials & PR Agencies"
        
        for region in regions:
            run_curator_session(niche, region, target_count=60)
            
        AGENT_STATUS = "Standby (Mission Complete)"
        LAST_RUN_LOG = f"Success: 300 sites pushed to Webhook on {time.ctime()}"
    except Exception as e:
        AGENT_STATUS = f"ERROR: {str(e)}"
        LAST_RUN_LOG = f"Crash Report: {str(e)}"

@app.route('/start', methods=['POST'])
def start_agent():
    """Triggered by n8n or any automation daily."""
    global AGENT_STATUS
    if "Running" in AGENT_STATUS:
        return jsonify({"Status": "Blocked", "Message": "Agent is already busy running a task."}), 409
    
    # Start the task in the background
    thread = threading.Thread(target=daily_task_wrapper)
    thread.daemon = True
    thread.start()
    
    return jsonify({"Status": "Agent Started", "Message": "300-site curation is now running in the background."})

@app.route('/health', methods=['GET'])
def health_check():
    """Checks Agent and Gemini API health."""
    try:
        # Check Gemini Key
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        client.models.generate_content(model='gemini-flash-latest', contents="ping")
        gemini_status = "Connected (Healthy)"
    except Exception as e:
        if "429" in str(e): gemini_status = "Quota Exhausted (429)"
        elif "403" in str(e): gemini_status = "Key Expired/Invalid (403)"
        else: gemini_status = f"Error: {str(e)}"

    return jsonify({
        "System": "Intelligent Outreach Agent V1",
        "Agent Status": AGENT_STATUS,
        "Gemini API": gemini_status,
        "Memory Bank Size": f"{os.path.getsize('/Users/sakshiagarwal/Desktop/Extracting Mails/master_scraped_domains.txt')} bytes",
        "Last Log": LAST_RUN_LOG
    })

if __name__ == "__main__":
    # Port 5000 is default for Flask - perfect for Docker/n8n
    print("🚀 INTELLIGENT AGENT API: LIVE ON PORT 5000.")
    app.run(host='0.0.0.0', port=5000)
