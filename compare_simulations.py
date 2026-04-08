#!/usr/bin/env python3
"""
Runs two simulations of the same product with different swarm sizes
and prints a side-by-side comparison of the results.

Usage:
    python compare_simulations.py
"""

import json
import time
import urllib.request
import urllib.error
import sys

API_URL = "http://127.0.0.1:8000"

# ── Product: FocusDesk ────────────────────────────────────────────────────────
# A realistic B2C SaaS — productivity timer with AI distraction blocking.
# Chosen because it has a clear split: some people love it, some don't need it.

PRODUCT = {
    "name": "FocusDesk",
    "description": """
        FocusDesk is a distraction-blocking productivity timer for remote workers
        and freelancers who struggle to stay focused during deep work sessions.

        The app uses AI to learn your distraction patterns — the exact websites,
        apps, and notification triggers that pull you out of flow — and blocks
        them automatically when a focus session starts. No manual site lists.
        No willpower required.

        Key features:
        - AI-powered distraction profile: learns what breaks YOUR focus, not a generic list
        - Pomodoro + custom timer modes with adaptive break reminders
        - Daily focus score and weekly trend reports
        - Team mode: share focus hours with your manager or accountability partner
        - Works on Mac, Windows, iOS, and Android — one subscription, all devices

        Pricing: $12/month or $89/year. 21-day free trial, no credit card required.
        Competing with: Freedom ($8/mo, no AI), Cold Turkey (one-time $39, no mobile),
        RescueTime ($12/mo, tracking only — no blocking).
    """,
    "price_usd": 12.0,
    "channel": "social_media",
    "target_market": "Remote workers and freelancers, 25–45 years old, who work from home and struggle with self-discipline and distraction during deep work hours",
}

RUNS = [
    {"num_agents": 10, "label": "RUN A — 10 agents"},
    {"num_agents": 15, "label": "RUN B — 15 agents"},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(
        f"{API_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:    detail = json.loads(raw).get("detail", raw)
        except: detail = raw
        print(f"\n[ERROR] {method} {path} → HTTP {e.code}: {detail}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Cannot reach backend at {API_URL}")
        print(f"        {e.reason}")
        sys.exit(1)


def submit(product):
    return api("POST", "/api/simulate", {"product": product})["simulation_id"]


def poll(sim_id, label):
    spinner = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    tick = 0
    while True:
        s = api("GET", f"/api/results/{sim_id}/status")
        st = s["status"]
        print(
            f"  {spinner[tick % len(spinner)]}  [{label}]  {st.upper():<10}  "
            f"personas={s['persona_count']:>2}  "
            f"interactions={s['interaction_count']:>2}  "
            f"posts={s['post_count']:>2}   ",
            end="\r",
        )
        tick += 1
        if st == "completed":
            print()
            return api("GET", f"/api/results/{sim_id}")
        if st == "failed":
            print(f"\n[FAILED] {s.get('error')}")
            sys.exit(1)
        time.sleep(4)


def bar(value, total, width=20):
    filled = int(round(value / total * width)) if total else 0
    return "█" * filled + "░" * (width - filled)


def pct(n, total):
    return f"{n/total*100:.0f}%" if total else "0%"


def sentiment_label(s):
    if s >= 0.5:  return "enthusiastic"
    if s >= 0.2:  return "positive"
    if s >= -0.1: return "neutral"
    if s >= -0.4: return "negative"
    return "hostile"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("═" * 66)
    print("  LaunchSim — FocusDesk  |  10-agent vs 15-agent comparison")
    print("═" * 66)
    print(f"  Product  : {PRODUCT['name']}")
    print(f"  Price    : ${PRODUCT['price_usd']:.2f}/mo")
    print(f"  Channel  : {PRODUCT['channel']}")
    print()

    results = []

    # ── Run simulations sequentially ─────────────────────────────────────────
    for run in RUNS:
        product = {**PRODUCT, "num_agents": run["num_agents"]}
        print(f"  Submitting {run['label']} ...")
        sim_id = submit(product)
        print(f"  ID: {sim_id}")
        result = poll(sim_id, run["label"])
        result["_label"]  = run["label"]
        result["_agents"] = run["num_agents"]
        results.append(result)
        print(f"  Done.\n")

    # ── Side-by-side comparison ───────────────────────────────────────────────
    a, b = results[0], results[1]
    ma, mb = a["metrics"], b["metrics"]

    print()
    print("═" * 66)
    print("  COMPARISON")
    print("═" * 66)
    print(f"  {'':30}  {'10 agents':>12}  {'15 agents':>12}")
    print("─" * 66)

    # Funnel
    for label, ka, kb in [
        ("Viewed",    "agents_who_viewed",    "agents_who_viewed"),
        ("Clicked",   "agents_who_clicked",   "agents_who_clicked"),
        ("Purchased", "agents_who_purchased", "agents_who_purchased"),
    ]:
        va = ma[ka]; pa = pct(va, ma["total_agents"])
        vb = mb[kb]; pb = pct(vb, mb["total_agents"])
        print(f"  {label:<30}  {f'{va} ({pa})':>12}  {f'{vb} ({pb})':>12}")

    print("─" * 66)
    print(f"  {'Conversion rate':<30}  {ma['overall_conversion_rate']*100:>11.1f}%  {mb['overall_conversion_rate']*100:>11.1f}%")
    print(f"  {'Avg sentiment':<30}  {ma['average_sentiment']:>+12.2f}  {mb['average_sentiment']:>+12.2f}")
    sent_a = sentiment_label(ma['average_sentiment'])
    sent_b = sentiment_label(mb['average_sentiment'])
    print(f"  {'':30}  {f'({sent_a})':>12}  {f'({sent_b})':>12}")

    # Adoption peak
    curve_a = ma["adoption_curve"]
    curve_b = mb["adoption_curve"]
    peak_a = next((p for p in reversed(curve_a) if p["cumulative_purchases"] > 0), None)
    peak_b = next((p for p in reversed(curve_b) if p["cumulative_purchases"] > 0), None)
    last_buy_a = f"{peak_a['hour']}h" if peak_a else "none"
    last_buy_b = f"{peak_b['hour']}h" if peak_b else "none"
    print(f"  {'Last purchase at':<30}  {last_buy_a:>12}  {last_buy_b:>12}")
    print("─" * 66)

    # Social posts
    n_posts_a = len(a["social_posts"])
    n_posts_b = len(b["social_posts"])
    print(f"  {'Social posts generated':<30}  {n_posts_a:>12}  {n_posts_b:>12}")
    print("═" * 66)

    # ── Personas per run ──────────────────────────────────────────────────────
    for result in results:
        print()
        print(f"  PERSONAS — {result['_label']}")
        print("─" * 66)
        purchased_ids = {
            i["agent_id"]
            for i in result["interactions"]
            if i["interaction_type"] == "purchased"
        }
        for p in result["personas"]:
            wtp      = p["willingness_to_pay_usd"]
            price    = PRODUCT["price_usd"]
            bought   = p["agent_id"] in purchased_ids
            decision = "BOUGHT  " if bought else ("WTP LOW " if wtp < price else "BOUNCED ")
            print(
                f"  {p['agent_id']}  {p['name']:<20}  {p['archetype']:<16}  "
                f"WTP=${wtp:<5.0f}  [{decision}]"
            )
        print()

    # ── Objections comparison ─────────────────────────────────────────────────
    print()
    for result in results:
        print(f"  TOP OBJECTIONS — {result['_label']}")
        print("─" * 66)
        for i, obj in enumerate(result["metrics"]["top_objections"], 1):
            print(f"  #{i}  [{obj['frequency']}x]  {obj['objection'][:70]}")
        print()

    # ── Social posts per run ──────────────────────────────────────────────────
    for result in results:
        print(f"  SOCIAL POSTS — {result['_label']}")
        print("─" * 66)
        for post in result["social_posts"][:2]:
            s = post["sentiment"]
            print(f"  [{post['platform'].upper()}]  sentiment={s:+.2f} ({sentiment_label(s)})  upvotes={post['upvotes']}")
            print(f"    {post['content'][:200]}")
            print()

    # ── Strategic insights comparison ─────────────────────────────────────────
    for result in results:
        print(f"  INSIGHTS — {result['_label']}")
        print("─" * 66)
        for i, insight in enumerate(result["metrics"]["key_insights"], 1):
            print(f"  {i}. {insight[:120]}")
        print()

    # ── Simulation IDs for further exploration ────────────────────────────────
    print("═" * 66)
    print("  SIMULATION IDs (explore further via API or dashboard)")
    print("─" * 66)
    for r in results:
        print(f"  {r['_label']}")
        print(f"    Results    →  GET {API_URL}/api/results/{r['simulation_id']}")
        print(f"    Dashboard  →  http://localhost:3000/simulation/{r['simulation_id']}")
    print("═" * 66)
    print()


if __name__ == "__main__":
    main()
