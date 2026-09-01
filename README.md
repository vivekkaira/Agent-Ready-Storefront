# 🛒 Agent-Ready Storefront

Built for **Razorpay Buildathon — Track 01: AI Growth & Agentic Commerce**

An AI-powered storefront that does two things at once:
1. Makes a merchant **transactable by an AI buyer agent**, end to end, using Razorpay's test-mode APIs.
2. Uses a **growth agent** to proactively grow revenue through relevant upsell suggestions.

Every money-moving action is **explainable, bounded, and gated** — with a full audit trail and graceful handling of failures (out-of-stock items, rejected approvals).

---

## ✨ Features

- **Agent-readable catalog** — 100 real, structured products (via [DummyJSON](https://dummyjson.com))
- **AI buyer agent** — understands natural-language requests and picks the best matching product, with a visible reason for every pick
- **Gated checkout** — purchases under ₹7000 auto-approve; anything above requires manual confirmation before any payment is attempted
- **Real Razorpay test-mode orders** — actual API calls, not mocked
- **Growth agent** — suggests one relevant, complementary upsell after every successful purchase
- **Graceful failure handling**:
  - Out-of-stock items are blocked *before* any payment attempt
  - Rejected approvals are logged cleanly, no crash
- **Full audit trail** — every decision (product picked, gate outcome, order ID, timestamps) is logged to `audit_log.json` and rendered live in the UI
- **Two ways to run it**: a terminal flow (`main.py`) and a browser demo UI (`app.py`, built with Streamlit)

---

## 🏗️ How it works

```
User request
     │
     ▼
AI buyer agent (Gemini) — picks a product from the catalog + explains why
     │
     ▼
Gate check — auto-approve under ₹3000, else ask for manual approval
     │
     ▼
Razorpay test-mode order created
     │
     ▼
Growth agent (Gemini) — suggests one complementary upsell
     │
     ▼
Upsell (if accepted) goes through the same gate check + checkout
     │
     ▼
Every step logged to the audit trail
```

---

## 🛠️ Tech stack

- **Python 3**
- **Google Gemini API** (`gemini-3.5-flash-lite`) — powers both the buyer agent and growth agent
- **Razorpay API** (test mode) — order creation
- **Streamlit** — browser demo UI
- **DummyJSON** — free product data API for the catalog

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/vivekkaira/Agent-Ready-Storefront.git
cd Agent-Ready-Storefront
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your own API keys
Create a `.env` file in the project root:
```
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_key_secret_here
GEMINI_API_KEY=your_gemini_key_here
```
- Get free Razorpay test keys at [razorpay.com](https://razorpay.com) → Dashboard → Test Mode → API Keys
- Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com)

---

## ▶️ Running it

**Terminal version:**
```bash
python main.py
```

**Browser demo (recommended for judges):**
```bash
streamlit run app.py
```
Opens automatically at `http://localhost:8501`

---

## 📋 Audit trail

Every run appends to `audit_log.json`, capturing:
- The original user request
- Which product the agent picked and why
- The gate decision (auto-approved / needs approval / blocked) and reason
- The final outcome and Razorpay order ID (if created)
- Growth agent suggestions and whether they were accepted

This is rendered live as a readable timeline inside the Streamlit app.

---

## 🎯 Test scenarios to try

- `"I need a phone accessory"` → normal auto-approved purchase
- `"I want the most expensive item you have"` → triggers manual approval gate
- Anything matching an out-of-stock item → graceful block, no payment attempted

---

## ⚠️ Notes

- This runs entirely in **Razorpay test mode** — no real payments occur
- `.env` and `venv/` are excluded from version control via `.gitignore`
