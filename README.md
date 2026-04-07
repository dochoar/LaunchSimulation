<div align="center">

<h1>🚀 LaunchSim</h1>

<p>
<em>A Product Launch Simulation Engine, Predicting Market Responses</em>
</p>

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)

</div>

**LaunchSim** is a next-generation market prediction engine powered by multi-agent technology. By inputting your product features and target audience, it automatically constructs a high-fidelity parallel digital market. Within this space, dozens of intelligent virtual personas—driven by **OpenAI's Large Language Models (LLMs)** and orchestrated through **LangChain & LangGraph**—with independent occupations, pain points, willingness to pay, and cognitive biases freely interact and evaluate your startup launch. You can inject pricing variables dynamically to precisely deduce product-market fit — **rehearse your product launch in a digital sandbox, and win real markets after countless simulations**.

> You only need to: Define your product (name, price, description) and execute the test.</br>
> LaunchSim will return: A detailed prediction of interactions (purchases, skips) and a high-fidelity digital market response.

LaunchSim is dedicated to creating a swarm intelligence mirror that maps the reality of consumer behavior. We break through the limitations of traditional market research:

- **At the Macro Level**: We are a rehearsal laboratory for founders and product managers, allowing pricing strategies and feature rollouts to be tested at zero risk.
- **At the Micro Level**: We are a sandbox for deeply analyzing individual user adoption—letting every persona archetype evaluate your product organically.

From serious market validation to finding the optimal price point, we let every "what if" see its outcome.

### ⚙️ Simulation Engine Features

1. **Powered by OpenAI & LangGraph**: State-of-the-art LLMs synthesize the product value proposition and emulate complex human cognitive behaviors safely and interactively.
2. **Persona Generation**: Creates diverse archetypes (Early Adopters, Skeptics, Power Users) injected with specific pain points, tech-savviness, and annual income metrics.
3. **Environment Setup**: Fully configured FastAPI backend utilizing ChromaDB vector stores mapped against consumer behavioral models.
4. **Behavioral Simulation**: Agents synthesize product details and act on cognitive biases to make purchase decisions dynamically.

---

### 🚀 Getting Started (Source Code Deployment)

#### Prerequisites

| Tool | Version | Description | Check Installation |
|------|---------|-------------|-------------------|
| **Node.js** | 18+ | Frontend runtime, includes npm | `node -v` |
| **Python** | 3.11+ | Backend runtime | `python --version` |

#### 1. Configure Environment Variables

```bash
# Copy the example configuration file
cp backend/.env.example backend/.env

# Edit the .env file and fill in required LLM API keys for the agent logic
```

**Required Environment Variables:**

```env
# LLM API Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

#### 2. Install Dependencies

You can install all frontend and backend dependencies easily:

```bash
# Install frontend dependencies in the root (alias for frontend install)
npm run setup

# Install backend dependencies (uses pip and requirements.txt)
npm run install:backend
```

#### 3. Start Services

```bash
# Start both Next.js frontend and FastAPI backend concurrently
npm run dev
```

**Service URLs:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

### 🧪 Running Simulations

You can run simulations in one of two ways: either programmatically via Python scripts (for quick head-less testing), or through the complete Web Dashboard.

#### 1. Running an Example Simulation in the Terminal
We provide historical simulation models (like the **Quibi Launch Failure**) that you can execute directly in your terminal to see the AI reasoning and interaction metrics textually without needing a UI.

```bash
# Ensure you are at the project root
cd LaunchSim

# Execute the simulation using the backend's environment
backend/.venv/bin/python examples/quibi_simulation.py
```

#### 2. Running the Complete Visual Simulation
To run the full-fledged simulation with visual metrics, adoption curves, and LangGraph multi-agent analysis (`Cronista` agent summaries), you should start the entire React/FastAPI stack:

```bash
# Start both Next.js frontend and FastAPI backend concurrently
npm run dev
```
Then navigate your browser to `http://localhost:3000`. Here you can define your custom product parameters, launch it, and watch the agents react dynamically through the interactive dashboard.

---

## 🛠 Available Scripts

In the root `package.json`:
- `npm run dev`: Runs both frontend and backend 
- `npm run dev:backend`: Runs backend server 
- `npm run dev:frontend`: Runs frontend server 
- `npm run install:frontend` or `npm run setup`: Installs frontend dependencies 
- `npm run install:backend`: Installs backend dependencies 