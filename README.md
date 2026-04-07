<div align="center">

<h1>🚀 LaunchSim</h1>

<p>
<em>A Product Launch Simulation Engine — Rehearse your product launch in a digital sandbox</em>
</p>

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-FF6F00?style=flat-square)](https://langchain.ai/)

</div>

---

## 🤔 What is LaunchSim?

LaunchSim is a **multi-agent market simulation engine** that predicts how a product launch will perform in the real world. It creates a "parallel digital market" with intelligent virtual personas that interact with your product, generating realistic purchase decisions, social media posts, and strategic metrics.

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Your Product (Idea)                               │
│              Name, price, description, target market                    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT PIPELINE (LangGraph)                            │
│                                                                          │
│  1. 🔍 RESEARCHER    → Searches market info, competitors               │
│                         analyzes complaints and industry prices         │
│                                                                          │
│  2. 👤 ETHNOGRAPHER  → Generates N realistic virtual personas          │
│                        with demographics, archetypes, pain points       │
│                                                                          │
│  3. 🧠 POPULATOR     → Indexes each persona in vector store             │
│                        (ChromaDB) to enable RAG interviews              │
│                                                                          │
│  4. 🎯 LAUNCHER      → Simulates interactions: ignore → buy             │
│                        based on profile + price                         │
│                                                                          │
│  5. 💬 CONVERSATIONALIST → Generates social media posts                 │
│                        (Twitter, Reddit, Product Hunt)                  │
│                                                                          │
│  6. 📊 CHRONICLER    → Calculates metrics, adoption curve              │
│                        generates strategic insights                     │
│                                                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           RESULTS                                        │
│   • Conversion rate, adoption, sentiment                                 │
│   • Social media posts                                                  │
│   • Live interviews with generated personas                             │
│   • Strategic insights to improve your product                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗 System Architecture

### Tech Stack

| Component | Technology | Purpose |
|------------|------------|-----------|
| **Frontend** | Next.js 14 + React | UI to run simulations |
| **Backend** | FastAPI + Python 3.11+ | REST API + agent logic |
| **Orchestration** | LangGraph | Agent pipeline with shared state |
| **LLM** | Ollama (local) or OpenAI | Content generation and reasoning |
| **Vector Store** | ChromaDB | Persistent memory for each persona |
| **Database** | SQLite (aiosqlite) | Simulation results persistence |

### Data Flow

1. **User** sends product data (name, price, description)
2. **API** creates record in SQLite and returns `simulation_id`
3. **LangGraph** executes agent pipeline in background
4. **User** polls until simulation completes
5. **Results** include: personas, interactions, posts, metrics

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Check Command |
|------|---------|---------------|
| **Node.js** | 18+ | `node -v` |
| **Python** | 3.11+ | `python --version` |
| **Ollama** (optional) | Latest | `ollama --version` |

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/dochoar/LaunchSimulation.git
cd LaunchSimulation

# 2. Install dependencies
npm run setup          # Frontend (Next.js)
npm run install:backend # Backend (Python)

# 3. Configure environment
cp backend/.env.example backend/.env

# 4. Start services
npm run dev
```

### Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/simulate` | POST | Start simulation with product data |
| `/api/simulate/from-brief` | POST | Start simulation from free text |
| `/api/results/{simulation_id}` | GET | Get complete results |
| `/api/results/{simulation_id}/status` | GET | Get simulation status |
| `/api/results/{simulation_id}/personas` | GET | Get only generated personas |
| `/api/results/{simulation_id}/posts` | GET | Get only social posts |
| `/api/interview/{simulation_id}/agents` | GET | List agents for interview |
| `/api/interview/{simulation_id}/{agent_id}` | POST | Interview a persona |

---

## 🤖 The Agents Explained

### 1. Researcher
Searches real-time market information using DuckDuckGo. Generates 3 different queries (competitors, complaints, prices), executes parallel searches, verifies quality, and synthesizes results into a market context.

### 2. Ethnographer
Generates virtual personas based on market context. Each persona has: unique ID, demographics, archetype (early adopter, skeptic, etc.), pain points, objectives, cognitive biases, and willingness to pay (WTP).

### 3. Populator
Indexes each persona in ChromaDB to enable RAG interviews after simulation. Stores: identity, pain points, psychology, and bio.

### 4. Launcher
Simulates the conversion funnel:
- Ignored (30%) → Seen (25%) → Clicked (20%) → Read (12%) → Purchased (7%) → Abandoned (4%) → Shared (2%)

Uses archetypes to modify probabilities (early adopter ×2.5, skeptic ×0.2).

### 5. Conversationalist
For personas who interacted with the product, generates social media posts:
- Twitter (280 characters)
- Reddit (detailed)
- Product Hunt
- App Store

### 6. Chronicler
Calculates final metrics:
- KPIs: conversion, views, clicks, purchases
- Adoption curve (72 hours)
- Main objections (top 5)
- Strategic insights (3-5 recommendations)

### 7. Interviewer
Allows asking natural language questions to any generated persona. Uses RAG to search that persona's memory and respond in first person.

---

## 🧪 Usage Example

```python
import requests

# 1. Start simulation
response = requests.post("http://localhost:8000/api/simulate", json={
    "name": "My Product",
    "description": "An amazing solution for...",
    "price_usd": 29.99,
    "target_market": "Tech professionals",
    "num_agents": 50
})

simulation_id = response.json()["simulation_id"]

# 2. Wait for completion (polling)
import time
while True:
    status = requests.get(f"http://localhost:8000/api/results/{simulation_id}/status").json()
    if status["status"] == "completed":
        break
    time.sleep(2)

# 3. Get results
results = requests.get(f"http://localhost:8000/api/results/{simulation_id}").json()
print(results["metrics"])
```

---

## ⚙️ LLM Configuration

By default, LaunchSim uses **Ollama** (local, free). Edit `backend/.env`:

```env
# Ollama (local, recommended for Mac/Linux)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:7b

# Or OpenAI (cloud)
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
```

---

## 📁 Project Structure

```
LaunchSimulation/
├── backend/
│   ├── app/
│   │   ├── agents/          # The 6 system agents
│   │   ├── api/             # REST endpoints
│   │   ├── core/            # Config, LLM, DB
│   │   ├── models/          # Pydantic schemas + ORM
│   │   └── services/        # SimulationService, VectorStore
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                 # Next.js 14 app
│   ├── src/
│   │   ├── app/            # Pages and components
│   │   ├── components/     # UI components
│   │   └── lib/            # API client
│   └── package.json
│
├── package.json            # Development scripts
└── README.md
```

---

## 📄 License

MIT License — Feel free to use, modify, and share!

---

<div align="center">

**Questions? Issues? Pull Requests?**  
Excellent! This is an open source project. All contributions are welcome.

</div>