import sys
import os

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.agents.researcher import researcher_node
from app.models.schemas import ProductInput

def run():
    print("Testing Web Researcher Node...")
    product = ProductInput(
        name="Apple Vision Pro",
        description="A spatial computing headset blending digital content with physical space.",
        price_usd=3499.00
    )
    
    state = {
        "product": product,
        "market_research": None,
        "personas": [],
        "interactions": [],
        "error": None
    }
    
    result = researcher_node(state)
    print("\n--- Market Research Synthesized ---\n")
    print(result.get("market_research"))
    print("\n-----------------------------------\n")

if __name__ == "__main__":
    run()
