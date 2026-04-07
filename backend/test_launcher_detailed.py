#!/usr/bin/env python3
"""
Detailed test script to verify the launcher functionality with 10 agents using real data.
This version shows the actual reasoning to verify template usage.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.launcher import launcher_node
from app.models.schemas import (
    ProductInput,
    SimulatedAgentProfile,
    PainPoint,
    Archetype,
    InteractionType,
    Channel
)
from app.agents.state import SimulationState

def create_test_data():
    """Create test data with 10 agents of different archetypes."""
    
    # Create a test product
    product = ProductInput(
        name="LaunchSim Pro",
        description="A comprehensive simulation platform for startup launches",
        price_usd=29.99
    )
    
    # Create 10 agents with different archetypes and characteristics
    agents = [
        SimulatedAgentProfile(
            agent_id="agent_001",
            name="Alex Rivera",
            age=28,
            gender="Male",
            location="San Francisco, CA",
            occupation="Software Engineer",
            annual_income_usd=95000.0,
            archetype=Archetype.early_adopter,
            willingness_to_pay_usd=45.0,
            tech_savviness=9,
            pain_points=[
                PainPoint(topic="slow deployment processes", intensity=8),
                PainPoint(topic="lack of real-time collaboration", intensity=7)
            ],
            goals=["Reduce deployment time by 50%", "Improve team collaboration"],
            preferred_channels=[Channel.social_media, Channel.word_of_mouth, Channel.email],
            cognitive_biases=["novelty seeking", "social proof"],
            bio="Alex is a passionate software engineer who loves trying new tools that can improve development workflows. He's active in tech communities and often shares his findings with colleagues."
        ),
        SimulatedAgentProfile(
            agent_id="agent_002",
            name="Maria Chen",
            age=34,
            gender="Female",
            location="New York, NY",
            occupation="Product Manager",
            annual_income_usd=110000.0,
            archetype=Archetype.influencer,
            willingness_to_pay_usd=35.0,
            tech_savviness=8,
            pain_points=[
                PainPoint(topic="difficulty tracking user engagement", intensity=9),
                PainPoint(topic="manual reporting taking too much time", intensity=8)
            ],
            goals=["Better analytics dashboard", "Automate reporting processes"],
            preferred_channels=[Channel.social_media, Channel.email, Channel.other],
            cognitive_biases=["bandwagon effect", "authority bias"],
            bio="Maria is a product manager focused on user engagement and data-driven decision making. She needs tools that provide clear insights into user behavior and save time on reporting."
        ),
        SimulatedAgentProfile(
            agent_id="agent_003",
            name="James Wilson",
            age=42,
            gender="Male",
            location="Seattle, WA",
            occupation="DevOps Engineer",
            annual_income_usd=120000.0,
            archetype=Archetype.power_user,
            willingness_to_pay_usd=50.0,
            tech_savviness=9,
            pain_points=[
                PainPoint(topic="complex configuration setups", intensity=8),
                PainPoint(topic="poor monitoring and alerting", intensity=7)
            ],
            goals=["Simplify infrastructure configuration", "Implement comprehensive monitoring"],
            preferred_channels=[Channel.social_media, Channel.other, Channel.email],
            cognitive_biases=["status quo bias", "loss aversion"],
            bio="James is a senior DevOps engineer responsible for maintaining reliable and scalable infrastructure. He values tools that reduce complexity and provide strong observability."
        ),
        SimulatedAgentProfile(
            agent_id="agent_004",
            name="Sarah Johnson",
            age=31,
            gender="Female",
            location="Austin, TX",
            occupation="UX Designer",
            annual_income_usd=85000.0,
            archetype=Archetype.pragmatist,
            willingness_to_pay_usd=30.0,
            tech_savviness=7,
            pain_points=[
                PainPoint(topic="inconsistent design systems", intensity=7),
                PainPoint(topic="limited prototyping capabilities", intensity=6)
            ],
            goals=["Establish consistent design patterns", "Enhance prototyping features"],
            preferred_channels=[Channel.social_media, Channel.other, Channel.email],
            cognitive_biases=["confirmation bias"],
            bio="Sarah is a UX designer who advocates for user-centered design and consistent experiences. She looks for tools that help maintain design quality while improving efficiency."
        ),
        SimulatedAgentProfile(
            agent_id="agent_005",
            name="Tommy Lee",
            age=26,
            gender="Male",
            location="Boston, MA",
            occupation="Marketing Coordinator",
            annual_income_usd=55000.0,
            archetype=Archetype.casual_user,
            willingness_to_pay_usd=20.0,
            tech_savviness=5,
            pain_points=[
                PainPoint(topic="steep learning curves", intensity=6),
                PainPoint(topic="unclear ROI measurements", intensity=7)
            ],
            goals=["Easy-to-use interface", "Clear ROI tracking"],
            preferred_channels=[Channel.social_media, Channel.email, Channel.other],
            cognitive_biases=["present bias"],
            bio="Tommy is a marketing coordinator who needs tools that are easy to learn and demonstrate clear value. He prefers intuitive interfaces with straightforward analytics."
        ),
        SimulatedAgentProfile(
            agent_id="agent_006",
            name="Lisa Park",
            age=29,
            gender="Female",
            location="Chicago, IL",
            occupation="Financial Analyst",
            annual_income_usd=70000.0,
            archetype=Archetype.price_sensitive,
            willingness_to_pay_usd=15.0,
            tech_savviness=6,
            pain_points=[
                PainPoint(topic="expensive subscription models", intensity=9),
                PainPoint(topic="hidden fees and charges", intensity=8)
            ],
            goals=["Transparent pricing", "Cost-effective solutions"],
            preferred_channels=[Channel.social_media, Channel.other, Channel.email],
            cognitive_biases=["anchoring bias"],
            bio="Lisa is a financial analyst who carefully evaluates software investments. She prioritizes transparent pricing and dislikes unexpected costs or complex licensing models."
        ),
        SimulatedAgentProfile(
            agent_id="agent_007",
            name="Robert Kim",
            age=45,
            gender="Male",
            location="Los Angeles, CA",
            occupation="Operations Manager",
            annual_income_usd=80000.0,
            archetype=Archetype.conservative,
            willingness_to_pay_usd=25.0,
            tech_savviness=4,
            pain_points=[
                PainPoint(topic="resistance to change in teams", intensity=8),
                PainPoint(topic="lack of proven case studies", intensity=7)
            ],
            goals=["Minimal disruption during adoption", "Proven success stories"],
            preferred_channels=[Channel.email, Channel.other, Channel.word_of_mouth],
            cognitive_biases=["risk aversion", "system justification"],
            bio="Robert is an operations manager focused on team productivity and smooth operations. He prefers tools with minimal learning curve and proven track records in similar organizations."
        ),
        SimulatedAgentProfile(
            agent_id="agent_008",
            name="Emma Thompson",
            age=38,
            gender="Female",
            location="Denver, CO",
            occupation="Business Analyst",
            annual_income_usd=75000.0,
            archetype=Archetype.skeptic,
            willingness_to_pay_usd=18.0,
            tech_savviness=5,
            pain_points=[
                PainPoint(topic="overhyped tools that underdeliver", intensity=9),
                PainPoint(topic="poor integration capabilities", intensity=8)
            ],
            goals=["Verified performance claims", "Seamless integration options"],
            preferred_channels=[Channel.other, Channel.email, Channel.social_media],
            cognitive_biases=["skepticism", "belief bias"],
            bio="Emma is a business analyst who approaches new tools with healthy skepticism. She requires evidence-based claims and strong integration capabilities before considering adoption."
        ),
        SimulatedAgentProfile(
            agent_id="agent_009",
            name="David Rodriguez",
            age=33,
            gender="Male",
            location="Miami, FL",
            occupation="Startup Founder",
            annual_income_usd=90000.0,
            archetype=Archetype.early_adopter,
            willingness_to_pay_usd=40.0,
            tech_savviness=8,
            pain_points=[
                PainPoint(topic="limited runway for experimentation", intensity=8),
                PainPoint(topic="need for rapid validation", intensity=9)
            ],
            goals=["Fast experimentation cycles", "Quick validation methods"],
            preferred_channels=[Channel.social_media, Channel.other, Channel.email],
            cognitive_biases=["optimism bias", "overconfidence"],
            bio="David is a startup founder working with limited resources who needs to validate ideas quickly. He values tools that enable rapid experimentation and fast feedback loops."
        ),
        SimulatedAgentProfile(
            agent_id="agent_010",
            name="Jennifer Wu",
            age=27,
            gender="Female",
            location="San Jose, CA",
            occupation="Data Scientist",
            annual_income_usd=100000.0,
            archetype=Archetype.power_user,
            willingness_to_pay_usd=55.0,
            tech_savviness=9,
            pain_points=[
                PainPoint(topic="inefficient data pipelines", intensity=9),
                PainPoint(topic="lack of reproducible results", intensity=7)
            ],
            goals=["Streamline data workflows", "Ensure reproducibility"],
            preferred_channels=[Channel.social_media, Channel.other, Channel.email],
            cognitive_biases=["clustering illusion"],
            bio="Jennifer is a data scientist who works with complex datasets and needs reliable, reproducible results. She values tools that streamline data processing and support rigorous methodology."
        )
    ]
    
    # Create initial state
    state: SimulationState = {
        "product": product,
        "personas": agents,
        "interactions": [],
        "error": None
    }
    
    return state

def test_launcher_detailed():
    """Test the launcher node with 10 agents and show detailed reasoning."""
    print("Testing launcher with 10 agents (detailed view)...")
    print("=" * 60)
    
    # Create test data
    state = create_test_data()
    
    print(f"Product: {state['product'].name}")
    print(f"Price: ${state['product'].price_usd}")
    print(f"Number of agents: {len(state['personas'])}")
    print()
    
    # Run the launcher
    try:
        result = launcher_node(state)
        
        # Check if there was an error
        if result.get("error"):
            print(f"ERROR: {result['error']}")
            return False
        
        # Get the interactions
        interactions = result.get("interactions", [])
        
        if not interactions:
            print("ERROR: No interactions generated")
            return False
        
        print(f"Generated {len(interactions)} interactions:")
        print("-" * 60)
        
        # Print all interactions with details
        for i, interaction in enumerate(interactions, 1):
            print(f"{i:2d}. Agent {interaction.agent_id} ({interaction.agent_id[-3:]}):")
            print(f"    Action: {interaction.interaction_type.value.upper()}")
            print(f"    Reasoning: {interaction.reasoning}")
            print()
        
        # Count interaction types
        interaction_counts = {}
        purchase_count = 0
        
        for interaction in interactions:
            itype = interaction.interaction_type.value
            interaction_counts[itype] = interaction_counts.get(itype, 0) + 1
            
            if itype == "purchased":
                purchase_count += 1
        
        # Print summary
        print("Interaction Summary:")
        print("-" * 30)
        for itype, count in sorted(interaction_counts.items()):
            percentage = (count / len(interactions)) * 100
            print(f"{itype.capitalize():<12}: {count:>2} agents ({percentage:>5.1f}%)")
        
        print()
        print(f"Total purchases: {purchase_count}/{len(interactions)}")
        
        # Verify we got reasonable results
        if purchase_count > len(interactions):
            print("ERROR: More purchases than agents")
            return False
            
        if len(interactions) != 10:
            print(f"WARNING: Expected 10 interactions, got {len(interactions)}")
        
        # Check if reasoning looks like it came from templates (fallback)
        template_based_count = 0
        for interaction in interactions:
            reasoning = interaction.reasoning
            # Check if reasoning contains typical template phrases
            if any(phrase in reasoning for phrase in [
                "As an early adopter",
                "Nothing in the copy convinced me",
                "I was interested until I saw the price",
                "I read through everything carefully",
                "I noticed it, but I prefer to wait",
                "This looked exactly like something my audience needs",
                "The feature set is exactly what I've been missing",
                "The headline caught my eye"
            ]):
                template_based_count += 1
        
        print(f"Template-based reasoning: {template_based_count}/{len(interactions)} agents")
        if template_based_count > 0:
            print("✅ Correctly fell back to template-based reasoning when LLM unavailable")
        
        print()
        print("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_launcher_detailed()
    sys.exit(0 if success else 1)