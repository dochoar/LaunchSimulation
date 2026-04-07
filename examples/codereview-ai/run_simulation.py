#!/usr/bin/env python3
"""
CodeReview AI — LaunchSim End-to-End Demo Script
-------------------------------------------------
Demonstrates the full simulation workflow:
  1. Submit a product to the simulation API
  2. Poll until the simulation completes
  3. Print key metrics, social posts, and strategic insights
  4. Interview one of the generated personas

Requirements: Python 3.8+ (stdlib only — no pip install needed)
Backend must be running at http://localhost:8000

Usage:
    python run_simulation.py

    # Point to a different API host:
    API_URL=http://localhost:8000 python run_simulation.py

    # Skip running a new simulation and load sample output instead:
    python run_simulation.py --sample
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

import os
API_URL = os.environ.get("API_URL", "http://localhost:8000")

PRODUCT = {
    "name": "CodeReview AI",
    "description": (
        "AI-powered code review assistant that integrates directly with GitHub and GitLab. "
        "When a developer opens a PR, CodeReview AI posts an automated review within 60 seconds "
        "covering logic errors, security vulnerabilities (OWASP Top 10), performance bottlenecks "
        "(N+1 queries, memory leaks), and architecture feedback. Every comment explains WHY it "
        "matters and shows a concrete fix. Mentorship Mode adds educational context for junior devs. "
        "Learns your team's coding standards from existing PRs in 2 weeks. Installs in 2 minutes — "
        "no new tools to learn. 14-day free trial, no credit card required. "
        "Solo plan $29/mo, Team plan $79/mo for up to 8 seats."
    ),
    "price_usd": 29.0,
    "channel": "social_media",
    "target_market": "Solo developers and small engineering teams (2-10 people) struggling with slow or inconsistent code reviews",
    "num_agents": 50,
}

POLL_INTERVAL_SECONDS = 4
SAMPLE_FILE = Path(__file__).parent / "sample_output.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def api_request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            detail = json.loads(error_body).get("detail", error_body)
        except json.JSONDecodeError:
            detail = error_body
        print(f"\n[ERROR] {method} {url} → HTTP {e.code}: {detail}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Cannot reach backend at {url}")
        print(f"        Is it running? Start it with: npm run dev:backend")
        print(f"        Reason: {e.reason}")
        sys.exit(1)

def hr(char: str = "─", width: int = 60) -> None:
    print(char * width)

def section(title: str) -> None:
    print()
    hr("═")
    print(f"  {title}")
    hr("═")

# ── Main workflow ─────────────────────────────────────────────────────────────

def run_live_simulation() -> dict:
    """Submit product, poll until done, return full result."""
    print("\n  Submitting product to simulation engine...")
    resp = api_request("POST", "/api/simulate", {"product": PRODUCT})
    sim_id = resp["simulation_id"]
    print(f"  Simulation ID : {sim_id}")
    print(f"  Status        : {resp['status']}")
    print(f"\n  Polling every {POLL_INTERVAL_SECONDS}s until complete...\n")

    dots = 0
    while True:
        status_resp = api_request("GET", f"/api/results/{sim_id}/status")
        status = status_resp["status"]

        print(
            f"  [{status.upper():10s}] "
            f"personas={status_resp['persona_count']:>3}  "
            f"interactions={status_resp['interaction_count']:>3}  "
            f"posts={status_resp['post_count']:>3}  "
            f"{'.' * (dots % 4)}   ",
            end="\r",
        )
        dots += 1

        if status == "completed":
            print()
            return api_request("GET", f"/api/results/{sim_id}")
        elif status == "failed":
            print(f"\n\n[FAILED] {status_resp.get('error', 'Unknown error')}")
            sys.exit(1)

        time.sleep(POLL_INTERVAL_SECONDS)


def load_sample() -> dict:
    """Load pre-computed sample output (no backend required)."""
    print("\n  Loading sample output (--sample mode, no backend required)")
    with open(SAMPLE_FILE) as f:
        return json.load(f)


def print_metrics(result: dict) -> None:
    section("SIMULATION METRICS")
    m = result["metrics"]
    p = result["product"]

    print(f"  Product       : {p['name']}  @  ${p['price_usd']:.2f}/mo")
    print(f"  Channel       : {p['channel']}")
    print(f"  Swarm size    : {m['total_agents']} agents\n")

    hr()
    print(f"  Viewed        : {m['agents_who_viewed']:>4} agents  ({m['agents_who_viewed']/m['total_agents']*100:.1f}%)")
    print(f"  Clicked       : {m['agents_who_clicked']:>4} agents  ({m['agents_who_clicked']/m['total_agents']*100:.1f}%)")
    print(f"  Purchased     : {m['agents_who_purchased']:>4} agents  ({m['agents_who_purchased']/m['total_agents']*100:.1f}%)")
    print(f"  Conversion    : {m['overall_conversion_rate']*100:.1f}%")
    print(f"  Avg Sentiment : {m['average_sentiment']:+.2f}  (-1 = hostile, +1 = enthusiastic)")
    hr()


def print_top_objections(result: dict) -> None:
    section("TOP MARKET OBJECTIONS")
    for i, obj in enumerate(result["metrics"]["top_objections"], 1):
        print(f"  #{i} [{obj['frequency']}x]  {obj['objection']}")
        agents = ", ".join(obj["example_agents"][:3])
        print(f"       ↳ Example agents: {agents}")
        print()


def print_social_posts(result: dict) -> None:
    section("SOCIAL FEED SAMPLE (3 posts)")
    posts = result["social_posts"][:3]
    for post in posts:
        platform = post["platform"].upper()
        sentiment = post["sentiment"]
        sentiment_label = "positive" if sentiment > 0.3 else ("negative" if sentiment < -0.2 else "neutral")
        print(f"  [{platform}]  sentiment={sentiment:+.2f} ({sentiment_label})  upvotes={post['upvotes']}")
        hr("-", 60)
        for line in post["content"].split(". "):
            print(f"    {line.strip()}.")
        if post["replies"]:
            print(f"\n  Top reply: \"{post['replies'][0]}\"")
        print()


def print_insights(result: dict) -> None:
    section("STRATEGIC INSIGHTS FROM THE AI CHRONICLER")
    for i, insight in enumerate(result["metrics"]["key_insights"], 1):
        print(f"\n  {i}. {insight}")
    print()


def print_personas_summary(result: dict) -> None:
    section("PERSONA SWARM OVERVIEW (first 5)")
    for p in result["personas"][:5]:
        wtp = p["willingness_to_pay_usd"]
        price = result["product"]["price_usd"]
        converts = "BUYS" if wtp >= price else "BOUNCES"
        print(
            f"  {p['agent_id']}  {p['name']:<20}  {p['archetype']:<15}  "
            f"WTP=${wtp:<6.0f}  [{converts}]"
        )
        print(f"           {p['bio'][:90]}...")
        print()


def run_interview(result: dict) -> None:
    """Interview the first agent who purchased."""
    sim_id = result["simulation_id"]

    # Find a purchased agent from interactions
    purchased = [
        i["agent_id"]
        for i in result["interactions"]
        if i["interaction_type"] == "purchased"
    ]
    if not purchased:
        print("\n  No purchased agents to interview in this simulation run.")
        return

    agent_id = purchased[0]
    persona = next((p for p in result["personas"] if p["agent_id"] == agent_id), None)
    name = persona["name"] if persona else agent_id

    section(f"LIVE INTERVIEW: {name} ({agent_id})")
    question = "Why did you decide to buy CodeReview AI? What was the deciding factor?"
    print(f"  Q: {question}\n")

    resp = api_request(
        "POST",
        f"/api/interview/{sim_id}/{agent_id}",
        {"question": question},
    )
    print(f"  A ({resp['agent_name']}): {resp['answer']}")
    print(f"\n  Purchased : {resp['purchased']}")
    print(f"  Summary   : {resp['reasoning_summary']}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    use_sample = "--sample" in sys.argv

    hr("═")
    print("  LaunchSim — CodeReview AI Market Simulation")
    hr("═")

    if use_sample:
        result = load_sample()
    else:
        result = run_live_simulation()

    print_metrics(result)
    print_personas_summary(result)
    print_top_objections(result)
    print_social_posts(result)
    print_insights(result)

    if not use_sample:
        run_interview(result)
    else:
        print("\n  (Skipping live interview — run without --sample against a live backend)")

    section("DONE")
    print(f"  Full results: GET {API_URL}/api/results/{result['simulation_id']}")
    print(f"  API docs    : {API_URL}/docs")
    print()


if __name__ == "__main__":
    main()
