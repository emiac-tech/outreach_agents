# 🛠️ Server Setup Guide: Intelligent Outreach Agent
**For the EMiac-Tech Developer Team**

This guide explains how to deploy the Gemini-driven curation agent on your dedicated server.

---

### 📋 1. Prerequisites (What you need on the server)
*   **Python:** Version 3.10 or higher.
*   **Git:** Installed and configured.
*   **Environment:** A dedicated directory (e.g., `/home/outreach/agent`).

---

### 📦 2. Clone & Initial Setup
Run these commands on your server:

```bash
# Clone the repository
git clone https://github.com/emiac-tech/outreach_agents.git
cd outreach_agents

# Create and activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

### 🧠 3. Intelligence & API Keys (Critical)
Create a `.env` file in the root folder:

```bash
touch .env
```

**Inside the `.env`, add your Gemini API Key:**
`GEMINI_API_KEY=AIzaSyA2Tnl4Q7ZflSX-GOrJSR5DAB5NJpLmeCQ`

---

### 🛡️ 4. Google Sheets & Webhook Setup
*   **Service Account:** Place your `.json` service account file in the folder (e.g., `credentials.json`).
*   **Configuration:** Update the following variables in `gemini_intelligent_curator.py`:
    *   `SERVICE_ACCOUNT_FILE`: The full path to your `.json`.
    *   `GOOGLE_SHEET_ID`: `1H-2TBmVdoWwuHaxU671h0_gpkLApWEBdp789HITC7hQ`
    *   `WEBHOOK_URL`: `https://flow.emiactech.com/webhook/receivers-hook`

---

### 🐳 5. Recommended: Docker Deployment (Fast & Clean)
Using Docker ensures the agent runs identically on your server without dependency conflicts.

```bash
# 1. Clone & Setup
git clone https://github.com/emiac-tech/outreach_agents.git
cd outreach_agents

# 2. Build and Start the container
# Ensure your .env and credentials.json are in this folder
docker-compose up --build -d

# 3. View Logs (Watch the Brainstorming happen)
docker logs -f intelligent-outreach-curator
```

### 🚀 6. Traditional Deployment (Non-Docker)
To run the agent manually:
```bash
python3 gemini_intelligent_curator.py
```

**To schedule it daily (Automation):**
Use a `crontab` to find 100 new sites every morning at 9:00 AM:
```bash
0 9 * * * /path/to/venv/bin/python3 /path/to/outreach_agents/gemini_intelligent_curator.py
```

---

### 🚦 7. Monitoring & Logs
*   **Memory Bank:** The script uses `master_scraped_domains.txt` to remember all processed sites. This is mapped via Docker volumes so your data persists even if the container restarts. **Do not delete this file.**
*   **Logs:** Any errors will be visible in `docker logs`.

**Everything is now ready for production launch.**
