#!/usr/bin/env python3
# =============================================================================
#
#   LaunchSim — Market Simulation Script
#
#   1. Create an input.txt file with your product details (see input_example.txt)
#   2. Make sure the backend is running:  npm run dev:backend
#   3. Run this script:                   python simulate.py
#
# =============================================================================


import json
import sys
import time
import urllib.error
import urllib.request
import os


# =============================================================================
#  SETTINGS — change only if your setup is non-standard
# =============================================================================

# URL where the LaunchSim backend is running
API_URL = "http://localhost:8000"

# Seconds between status checks while the simulation runs
POLL_INTERVAL_SECONDS = 4

# How many social posts and insights to print in the summary
MAX_POSTS_TO_PRINT    = 3
MAX_INSIGHTS_TO_PRINT = 5


# =============================================================================
#  HELPER FUNCTIONS
# =============================================================================

def line(char="─", n=62):
    print(char * n)


def section(title):
    print()
    line("═")
    print(f"  {title}")
    line("═")


def validate_product(p: dict) -> None:
    errors = []
    if not p.get("name") or p["name"] == "Your Product Name":
        errors.append("  • Set a real product name (name in input.txt)")
    desc = (p.get("description") or "").strip()
    if len(desc) < 50:
        errors.append(f"  • Description is too short ({len(desc)} chars). Write at least 50.")
    if desc == "Replace this text with your product description.":
        errors.append("  • Replace the example description with your own product pitch")
    if not p.get("price_usd") or p["price_usd"] <= 0:
        errors.append("  • Set a price greater than 0 (price_usd in input.txt)")
    if errors:
        print("\n[STOP] Your product config needs a few changes before we can simulate:\n")
        for e in errors:
            print(e)
        print("\n  Edit input.txt and try again.\n")
        sys.exit(1)


def load_product_from_input() -> dict:
    """Load product configuration from input.txt"""
    input_path = "input.txt"
    if not os.path.exists(input_path):
        print(f"\n[ERROR] {input_path} not found.")
        print(f"        Please create {input_path} based on input_example.txt")
        print(f"        Example content:")
        print("")
        with open("input_example.txt", "r") as f:
            print(f.read())
        sys.exit(1)
    
    product = {}
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Split on first '=' to allow values containing '='
                if "=" not in line:
                    print(f"[WARNING] Line {line_num} in {input_path} malformed (no '='): {line}")
                    continue
                
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Handle special case for description: replace \n with actual newline
                if key == "description":
                    value = value.replace("\\n", "\n")
                
                product[key] = value
    except Exception as e:
        print(f"\n[ERROR] Failed to read {input_path}: {e}")
        sys.exit(1)
    
    # Set defaults for missing fields
    product.setdefault("name", "Your Product Name")
    product.setdefault("description", "Replace this text with your product description.")
    product.setdefault("price_usd", 29.0)
    product.setdefault("channel", "social_media")
    product.setdefault("target_market", "")
    product.setdefault("num_agents", 50)
    
    # Convert numeric fields
    try:
        product["price_usd"] = float(product["price_usd"])
    except ValueError:
        print(f"\n[ERROR] price_usd must be a number: {product['price_usd']}")
        sys.exit(1)
        
    try:
        product["num_agents"] = int(product["num_agents"])
    except ValueError:
        print(f"\n[ERROR] num_agents must be an integer: {product['num_agents']}")
        sys.exit(1)
    
    return product


def api(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(
        f"{API_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            detail = json.loads(raw).get("detail", raw)
        except json.JSONDecodeError:
            detail = raw
        print(f"\n[ERROR] {method} {path} → HTTP {e.code}: {detail}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Cannot reach the backend at {API_URL}")
        print(f"        Start it first with:  npm run dev:backend")
        print(f"        Reason: {e.reason}")
        sys.exit(1)


def main():
    # Load product configuration from input.txt
    PRODUCT = load_product_from_input()
    
    # Validate the loaded product
    validate_product(PRODUCT)

    line("═")
    print(f"  LaunchSim  ·  {PRODUCT['name']}")
    line("═")
    print(f"  Price      : ${PRODUCT['price_usd']:.2f}")
    print(f"  Channel    : {PRODUCT['channel']}")
    print(f"  Agents     : {PRODUCT['num_agents']} synthetic personas")
    if PRODUCT.get("target_market"):
        print(f"  Market     : {PRODUCT['target_market']}")

    # Submit
    print(f"\n  Submitting to {API_URL}/api/simulate ...")
    resp   = api("POST", "/api/simulate", {"product": PRODUCT})
    sim_id = resp["simulation_id"]
    print(f"  Simulation ID : {sim_id}")

    # Poll
    print(f"\n  Running simulation — this takes a few minutes.\n")
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    tick    = 0
    while True:
        s = api("GET", f"/api/results/{sim_id}/status")
        status = s["status"]
        print(
            f"  {spinner[tick % len(spinner)]}  {status.upper():<10}  "
            f"personas={s['persona_count']:>3}  "
            f"interactions={s['interaction_count']:>3}  "
            f"posts={s['post_count']:>3}   ",
            end="\r",
        )
        tick += 1
        if status == "completed":
            print()
            break
        if status == "failed":
            print(f"\n\n[FAILED] {s.get('error', 'Unknown error')}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)

    # Fetch full results
    result  = api("GET", f"/api/results/{sim_id}")
    metrics = result["metrics"]

    # Metrics
    section("RESULTS")
    total = metrics["total_agents"]
    print(f"  {'Viewed':<14}: {metrics['agents_who_viewed']:>4}  ({metrics['agents_who_viewed']/total*100:.1f}%)")
    print(f"  {'Clicked':<14}: {metrics['agents_who_clicked']:>4}  ({metrics['agents_who_clicked']/total*100:.1f}%)")
    print(f"  {'Purchased':<14}: {metrics['agents_who_purchased']:>4}  ({metrics['agents_who_purchased']/total*100:.1f}%)")
    print(f"  {'Conversion':<14}: {metrics['overall_conversion_rate']*100:.1f}%")
    print(f"  {'Avg sentiment':<14}: {metrics['average_sentiment']:+.2f}   (-1 hostile → +1 enthusiastic)")

    # Personas summary
    section("PERSONAS GENERATED (first 5)")
    for p in result["personas"][:5]:
        wtp      = p["willingness_to_pay_usd"]
        price    = PRODUCT["price_usd"]
        decision = "BUYS    " if wtp >= price else "BOUNCES "
        print(f"  {p['agent_id']}  {p['name']:<22} {p['archetype']:<16} WTP=${wtp:<7.0f} [{decision}]")
        print(f"           {p['bio'][:95]}...")
        print()

    # Top objections
    section("TOP OBJECTIONS")
    for i, obj in enumerate(metrics["top_objections"], 1):
        print(f"  #{i}  [{obj['frequency']}x]  {obj['objection']}")
        print()

    # Social posts
    section(f"SOCIAL POSTS (first {MAX_POSTS_TO_PRINT})")
    for post in result["social_posts"][:MAX_POSTS_TO_PRINT]:
        platform  = post["platform"].upper()
        sentiment = post["sentiment"]
        label     = "positive" if sentiment > 0.3 else ("negative" if sentiment < -0.2 else "neutral")
        print(f"  [{platform}]  sentiment={sentiment:+.2f} ({label})  upvotes={post['upvotes']}")
        line("-")
        print(f"    {post['content'][:280]}")
        if post.get("replies"):
            print(f'\n  Top reply: "{post["replies"][0]}"')
        print()

    # Strategic insights
    section("STRATEGIC INSIGHTS")
    for i, insight in enumerate(metrics["key_insights"][:MAX_INSIGHTS_TO_PRINT], 1):
        print(f"\n  {i}. {insight}")

    # Interview prompt
    section("DONE")
    print(f"  Full results  →  GET {API_URL}/api/results/{sim_id}")
    print(f"  API explorer  →  {API_URL}/docs")
    print(f"  Dashboard     →  http://localhost:3000/simulation/{sim_id}")
    print()
    print("  To interview a persona, run:")
    if result["personas"]:
        agent_id = result["personas"][0]["agent_id"]
        print(f"""
    import urllib.request, json
    resp = urllib.request.urlopen(
        urllib.request.Request(
            "{API_URL}/api/interview/{sim_id}/{agent_id}",
            data=json.dumps({{"question": "Why didn't you buy?"}}).encode(),
            headers={{"Content-Type": "application/json"}},
            method="POST",
        )
    )
    print(json.loads(resp.read())["answer"])
""")
    line("═")


if __name__ == "__main__":
    main()