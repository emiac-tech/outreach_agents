# 🚀 Intelligent Outreach Agent (Gemini Driven)
**High-Intelligence Middle East PR & SEO Curation System**

This repository contains the core orchestration engine for an intelligent outreach agent. Unlike standard scrapers, this system uses Gemini 1.5/2.0 AI to brainstorm, audit, and verify premium publishers across the MENA region.

## 🧠 Core Features:
1. **AI Brainstorming:** Gemini-driven domain discovery for any niche/region.
2. **AI Quality Critic:** Automated expert-level auditing to filter out link farms.
3. **Smart Extraction:** Scrapes direct pitching contacts while filtering generic department mailboxes.
4. **Memory Guard:** Uses a master domain bank to ensure 0% duplication.
5. **Real-Time Integration:** Simultaneously populates Google Sheets and triggers webhooks.

## 🛠️ Components:
- `gemini_intelligent_curator.py`: The main orchestrator.
- `gemini_brainstormer.py`: The domain discovery module.
- `gemini_critic.py`: The AI auditing engine.

## ⚙️ Quick Setup:
1. Clone this repository.
2. Create a `.env` file with your `GEMINI_API_KEY`.
3. Update `SERVICE_ACCOUNT_FILE` and `GOOGLE_SHEET_ID` in the orchestrator.
4. Run `python gemini_intelligent_curator.py`.

---
*Built for the EMiac-Tech SEO & Outreach Team.*
