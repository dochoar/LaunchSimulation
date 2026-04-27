<div align="center">

# LaunchSim

**Rehearse your product launch in a digital sandbox before spending a dollar.**

LaunchSim creates a swarm of synthetic personas powered by an LLM and simulates true swarm dynamics: agents influence each other through an accumulated social signal, so when an influencer buys or shares, it raises the odds for every agent that comes after — just like a real launch. Returns conversion metrics, social posts, market objections, and strategic insights — in minutes.

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-FF6F00?style=flat-square)](https://langchain.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>



---

## How to use it (3 steps)

### Step 1 — Install

```bash
git clone https://github.com/dochoar/LaunchSimulation.git
cd LaunchSimulation

npm run setup            # installs frontend dependencies
npm run install:backend  # installs Python backend dependencies
cp backend/.env.example backend/.env
```

Then open `backend/.env` and configure your LLM (see [LLM options](#llm-options) below).

---

### Step 2 — Describe your product

Create an `input.txt` file at the root of the project (see `input_example.txt` for reference). Edit the values to match your product:

```
name=Your Product Name
description=What problem does it solve, and who has that problem?
        How does your product solve it? (key features, not buzzwords)
        Why is the price fair? What makes you different from alternatives?
        Be specific — the more detail, the more realistic the simulation.
price_usd=29.0
channel=social_media
target_market=
num_agents=50
```

**Channel options:** `social_media` · `email` · `paid_ads` · `seo` · `word_of_mouth` · `app_store` · `other`

> 💡 Tip: Copy `input_example.txt` to `input.txt` and modify the values:
> ```bash
> cp input_example.txt input.txt
> ```

---

### Step 3 — Run

Open two terminals:

```bash
# Terminal 1 — start the backend
npm run dev:backend

# Terminal 2 — run your simulation
python simulate.py
```

That's it. The script reads your product details from `input.txt`, submits your product, polls until the simulation completes, and prints a full report in the terminal.

To also open the visual dashboard, start the full stack instead:

```bash
npm run dev   # starts both backend (8000) and frontend (3000)
```

Then go to http://localhost:3000 and use the web UI (which also reads from input.txt or lets you fill in a form).

---

## What you get

```
════════════════════════════════════════════════════════════════
  LaunchSim  ·  Your Product Name
════════════════════════════════════════════════════════════════
  Price      : $29.00
  Channel    : social_media
  Agents     : 50 synthetic personas

  ⠹  RUNNING      personas= 32  interactions=  0  posts=  0

════════════════════════════════════════════════════════════════
  RESULTS
════════════════════════════════════════════════════════════════
  Viewed        :   31  (62.0%)
  Clicked       :   18  (36.0%)
  Purchased     :    4  (8.0%)
  Conversion    : 8.0%
  Avg sentiment : +0.38   (-1 hostile → +1 enthusiastic)

════════════════════════════════════════════════════════════════
  PERSONAS GENERATED (first 5)
════════════════════════════════════════════════════════════════
  agent_001  Marcus Chen            early_adopter    WTP=$49     [BUYS    ]
             Senior engineer at Series B fintech. Drowning in PR review queue...

  agent_002  Priya Nair             pragmatist       WTP=$12     [BOUNCES ]
             Junior dev waiting 3 days for PR feedback. Price is a stretch...

════════════════════════════════════════════════════════════════
  TOP OBJECTIONS
════════════════════════════════════════════════════════════════
  #1  [14x]  Price point too high for individual devs — feels like a team tool
  #2  [9x]   Privacy concerns: proprietary code sent to external AI API

════════════════════════════════════════════════════════════════
  STRATEGIC INSIGHTS
════════════════════════════════════════════════════════════════
  1. Add a $15/mo solo tier — 14 non-buyers cited price as the only blocker
  2. Publish SOC 2 docs — 9 agents hard-blocked by security/privacy concerns
  3. Mentorship Mode is underused in marketing — junior devs love it but don't see it
```

---

## Writing a good description

The description is the most important field. It feeds the Researcher (who searches competitors and pricing) and the Ethnographer (who generates personas calibrated to your market).

**Include:**
- The specific problem — who has it, how often, how painful
- How your product solves it (concrete features, not "AI-powered innovation")
- The price and what they get for it
- What makes you different from tools they already use

**Good:**
> CodeReview AI posts an automated code review within 60 seconds of opening a PR on GitHub. It catches logic errors, security vulnerabilities (OWASP Top 10), N+1 queries, and explains every issue in plain English with a concrete fix. Includes Mentorship Mode for junior devs. Learns your team's coding standards in 2 weeks. $29/mo per seat, 14-day free trial. For engineering teams of 2–10 drowning in PR review backlog.

**Too vague:**
> An AI tool that helps developers write better code with advanced features and improve their workflow.

---

## LLM options

Edit `backend/.env` to switch models. Any OpenAI-compatible API works.

### Local — Ollama (free, private, no internet required)

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:7b

LLM_BOOST_API_KEY=ollama
LLM_BOOST_BASE_URL=http://localhost:11434/v1
LLM_BOOST_MODEL_NAME=qwen2.5:7b
```

Pull the model first:
```bash
ollama pull qwen2.5:7b
```

> 50 agents on a mid-range CPU: ~5–12 minutes.

### Cloud — OpenAI

```env
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

LLM_BOOST_API_KEY=sk-your-key-here
LLM_BOOST_BASE_URL=https://api.openai.com/v1
LLM_BOOST_MODEL_NAME=gpt-4o
```

> 50 agents: ~1–3 minutes. Cost: ~$0.10–0.30 per run with gpt-4o-mini.

### Other compatible providers

| Provider | `LLM_BASE_URL` | Notes |
|----------|---------------|-------|
| Groq | `https://api.groq.com/openai/v1` | Fast, generous free tier |
| Together AI | `https://api.together.xyz/v1` | Good open-source models |
| LM Studio | `http://localhost:1234/v1` | Local GUI alternative to Ollama |

---

## Tuning the simulation

All of these are in `simulate.py` — no need to touch the backend.

```python
"num_agents": 50,      # 10–30 = fast/rough, 50 = recommended, 100–200 = high confidence
"channel": "email",    # changes which social platforms personas prefer
"target_market": "...",# more specific → more varied, relevant personas
```

For deeper changes (conversion probabilities, persona archetypes, social post formats), see the [advanced customization](#advanced-customization) section below.

---

## Worked example

The `examples/codereview-ai/` folder contains a complete realistic simulation:

```bash
# See what output looks like — no backend needed:
python examples/codereview-ai/run_simulation.py --sample
```

It uses CodeReview AI ($29/mo, developer tooling) as the product and includes pre-computed realistic output showing 50 personas, 6 social posts, 5 objections, and 5 strategic insights.

---

## Visual dashboard

Start the full stack (`npm run dev`) and open http://localhost:3000 to use the web UI instead of the terminal script.

After a simulation runs you'll get:

- **Metrics cards** — conversion funnel at a glance
- **Adoption curve** — purchase velocity over 72 hours
- **Social feed** — all generated posts, filterable by platform and sentiment
- **Market Resistance** — top objections with frequency
- **Strategic Insights** — AI-generated recommendations
- **Persona interview panel** — ask any generated persona any question in natural language

---

## Advanced customization

### Change conversion probabilities

`backend/app/agents/launcher.py`:

```python
BASE_PROBABILITIES = {
    "ignored":   0.30,   # ← lower this to model high-awareness markets
    "viewed":    0.25,
    "clicked":   0.20,
    "read":      0.12,
    "purchased": 0.07,   # ← raise this for high-intent markets (e.g. enterprise inbound)
    "abandoned": 0.04,
    "shared":    0.02,
}
```

### Change archetype purchase multipliers

```python
ARCHETYPE_PURCHASE_MULTIPLIERS = {
    "early_adopter":   2.5,   # buys fast, forgives rough edges
    "pragmatist":      1.0,   # buys when clear ROI
    "conservative":    0.5,   # needs references, case studies
    "price_sensitive": 0.4,   # WTP is the main gate
    "skeptic":         0.2,   # rarely buys on first exposure
}
```

### Change persona batch size

`backend/app/agents/ethnographer.py`:

```python
BATCH_SIZE = 8    # increase to 15–20 if using GPT-4-class models
```

### Add a social media platform

`backend/app/agents/conversador.py`:

```python
PLATFORM_CONFIGS = {
    "twitter":      {"max_chars": 280,  "tone": "casual, punchy"},
    "reddit":       {"max_chars": 800,  "tone": "detailed, community-style"},
    "product_hunt": {"max_chars": 400,  "tone": "constructive, maker-friendly"},
    "app_store":    {"max_chars": 300,  "tone": "direct, star-rating style"},
    # Add your own platform here
}
```

---

## Project structure

```
LaunchSimulation/
│
├── simulate.py                     ← RUN HERE — after creating input.txt
│
├── backend/
│   ├── .env.example                ← copy to .env, configure your LLM
│   └── app/
│       ├── agents/
│       │   ├── graph.py            # LangGraph pipeline
│       │   ├── researcher.py       # market research (DuckDuckGo + LLM)
│       │   ├── ethnographer.py     # persona generation
│       │   ├── populator.py        # ChromaDB indexing
│       │   ├── launcher.py         # interaction simulation + conversion funnel
│       │   ├── conversador.py      # social post generation
│       │   ├── chronicler.py       # metrics + strategic insights
│       │   └── interviewer.py      # RAG-powered persona chat
│       ├── api/                    # REST endpoints (simulate, results, interview)
│       ├── core/                   # config, LLM factory, database
│       ├── models/                 # Pydantic schemas + SQLAlchemy ORM
│       └── services/               # simulation orchestration + vector store
│
├── src/                            # Next.js frontend
│   ├── app/page.tsx                # product submission form
│   ├── app/simulation/[id]/page.tsx # results dashboard
│   └── components/                 # metrics, chart, social feed, interview panel
│
├── examples/
│   └── codereview-ai/              # worked example with sample output
│       ├── product_brief.md
│       ├── run_simulation.py
│       └── sample_output.json      # pre-computed — view without running backend
│
└── package.json                    # npm run dev · dev:backend · dev:frontend
```

---

## API reference

If you prefer to call the API directly (curl, Postman, your own script):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/simulate` | POST | Start a simulation |
| `/api/simulate/from-brief` | POST | Start from free-text product description |
| `/api/results/{id}` | GET | Full results |
| `/api/results/{id}/status` | GET | Lightweight status poll |
| `/api/results/{id}/personas` | GET | Generated personas only |
| `/api/results/{id}/posts` | GET | Social posts only |
| `/api/interview/{id}/agents` | GET | List interviewable personas |
| `/api/interview/{id}/{agent_id}` | POST | Ask a persona a question |

Interactive docs: http://localhost:8000/docs

---

## FAQ

**How long does a simulation take?**
With Ollama (local, 7B model): 5–15 minutes for 50 agents depending on hardware.
With Groq or OpenAI: 1–3 minutes.

**How do I get more varied personas?**
Be more specific in `target_market`. "developers" produces similar personas. "junior backend developers in Southeast Asia earning under $30K" produces diverse, realistic ones.

**Where is data stored?**
- Simulation results: `backend/launchsim.db` (SQLite)
- Persona memories (for interviews): `backend/chroma_db/`

Delete both to reset everything.

**Does this send my product description to the internet?**
Only if you use a cloud LLM (OpenAI, Groq, etc.). With Ollama, everything runs locally and nothing leaves your machine.

---

## License

MIT — use it, fork it, ship it.
