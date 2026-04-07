#!/usr/bin/env python3
import sys
import os

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.agents.launcher import launcher_node
from app.models.schemas import (
    ProductInput,
    SimulatedAgentProfile,
    PainPoint,
    Archetype,
    InteractionType,
    Channel,
    DecisionAuthority
)
from app.agents.state import SimulationState

def create_quibi_data():
    product = ProductInput(
        name="Quibi",
        description="A mobile-only streaming app delivering 'Quick Bites' of high-budget Hollywood content in 10 minutes or less. Optimized entirely for smartphones with seamless vertical/horizontal orientation. Aimed at commuters.",
        price_usd=7.99
    )
    
    agents = [
        SimulatedAgentProfile(
            agent_id="agent_01",
            name="Chloe",
            age=22,
            gender="Female",
            location="Los Angeles, CA",
            occupation="Student",
            annual_income_usd=15000.0,
            archetype=Archetype.price_sensitive,
            willingness_to_pay_usd=0.0,
            tech_savviness=10,
            pain_points=[PainPoint(topic="Boredom during short breaks", intensity=7)],
            goals=["Quick entertainment", "Shareable content"],
            preferred_channels=[Channel.social_media],
            cognitive_biases=["social proof"],
            current_tools=["TikTok", "YouTube", "Instagram"],
            switching_cost_tolerance=1,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=1,
            network_influence=9,
            bio="Spends 4 hours a day on TikTok. Never pays for apps."
        ),
        SimulatedAgentProfile(
            agent_id="agent_02",
            name="Mark",
            age=31,
            gender="Male",
            location="New York, NY",
            occupation="Office Worker",
            annual_income_usd=70000.0,
            archetype=Archetype.pragmatist,
            willingness_to_pay_usd=4.0,
            tech_savviness=7,
            pain_points=[PainPoint(topic="Subscription fatigue", intensity=10)],
            goals=["Watch premium TV on big screen"],
            preferred_channels=[Channel.word_of_mouth],
            cognitive_biases=["loss aversion"],
            current_tools=["Netflix", "HBO Max", "YouTube"],
            switching_cost_tolerance=2,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=2,
            network_influence=3,
            bio="Already pays for huge streaming services. Likes YouTube on his phone for short videos."
        ),
        SimulatedAgentProfile(
            agent_id="agent_03",
            name="Sarah",
            age=26,
            gender="Female",
            location="Austin, TX",
            occupation="Designer",
            annual_income_usd=60000.0,
            archetype=Archetype.early_adopter,
            willingness_to_pay_usd=8.0,
            tech_savviness=8,
            pain_points=[PainPoint(topic="Lack of high quality short fiction", intensity=5)],
            goals=["Stay updated on pop culture"],
            preferred_channels=[Channel.social_media],
            cognitive_biases=["novelty seeking"],
            current_tools=["TikTok", "Netflix"],
            switching_cost_tolerance=6,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=5,
            network_influence=6,
            bio="Loves trying new apps. Might try Quibi for a month."
        ),
        SimulatedAgentProfile(
            agent_id="agent_04",
            name="David",
            age=35,
            gender="Male",
            location="Seattle, WA",
            occupation="Engineer",
            annual_income_usd=110000.0,
            archetype=Archetype.power_user,
            willingness_to_pay_usd=5.0,
            tech_savviness=9,
            pain_points=[PainPoint(topic="Commute is too long", intensity=8)],
            goals=["Productivity during commute"],
            preferred_channels=[Channel.other],
            cognitive_biases=["status quo bias"],
            current_tools=["Podcasts", "Twitter"],
            switching_cost_tolerance=3,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=3,
            network_influence=4,
            bio="Prefers listening to podcasts during commute so he doesn't have to stare at screen."
        ),
        SimulatedAgentProfile(
            agent_id="agent_05",
            name="Elena",
            age=20,
            gender="Female",
            location="Miami, FL",
            occupation="Barista",
            annual_income_usd=25000.0,
            archetype=Archetype.casual_user,
            willingness_to_pay_usd=0.0,
            tech_savviness=8,
            pain_points=[PainPoint(topic="Bored between shifts", intensity=6)],
            goals=["Laugh at funny videos"],
            preferred_channels=[Channel.social_media],
            cognitive_biases=["bandwagon effect"],
            current_tools=["TikTok", "Snapchat"],
            switching_cost_tolerance=2,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=1,
            network_influence=7,
            bio="Doesn't have disposable income for entertainment."
        ),
        SimulatedAgentProfile(
            agent_id="agent_06",
            name="James",
            age=28,
            gender="Male",
            location="Chicago, IL",
            occupation="Sales",
            annual_income_usd=80000.0,
            archetype=Archetype.skeptic,
            willingness_to_pay_usd=0.0,
            tech_savviness=6,
            pain_points=[PainPoint(topic="Hard to find good shows", intensity=4)],
            goals=["Relax after work"],
            preferred_channels=[Channel.word_of_mouth],
            cognitive_biases=["skepticism"],
            current_tools=["Netflix", "Spotify"],
            switching_cost_tolerance=2,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=2,
            network_influence=5,
            bio="Doesn't understand why he would pay for 10 minute videos."
        ),
        SimulatedAgentProfile(
            agent_id="agent_07",
            name="Alex",
            age=24,
            gender="Non-binary",
            location="Portland, OR",
            occupation="Freelancer",
            annual_income_usd=40000.0,
            archetype=Archetype.influencer,
            willingness_to_pay_usd=5.0,
            tech_savviness=9,
            pain_points=[PainPoint(topic="Want to make viral content", intensity=9)],
            goals=["Share clips with friends"],
            preferred_channels=[Channel.social_media],
            cognitive_biases=["social proof"],
            current_tools=["TikTok", "YouTube Creators"],
            switching_cost_tolerance=4,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=3,
            network_influence=8,
            bio="If they can't screenshot or share the content easily, they won't use it."
        ),
        SimulatedAgentProfile(
            agent_id="agent_08",
            name="Robert",
            age=40,
            gender="Male",
            location="Denver, CO",
            occupation="Manager",
            annual_income_usd=130000.0,
            archetype=Archetype.conservative,
            willingness_to_pay_usd=15.0,
            tech_savviness=5,
            pain_points=[PainPoint(topic="Not enough time for movies", intensity=6)],
            goals=["Watch quick content on weekend"],
            preferred_channels=[Channel.paid_ads],
            cognitive_biases=["anchoring bias"],
            current_tools=["Amazon Prime"],
            switching_cost_tolerance=1,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=1,
            network_influence=3,
            bio="Prefers to watch TV on his 65 inch TV, rarely watches video on phone."
        ),
        SimulatedAgentProfile(
            agent_id="agent_09",
            name="Mia",
            age=29,
            gender="Female",
            location="Boston, MA",
            occupation="Nurse",
            annual_income_usd=75000.0,
            archetype=Archetype.casual_user,
            willingness_to_pay_usd=4.99,
            tech_savviness=7,
            pain_points=[PainPoint(topic="Stressed during breaks", intensity=8)],
            goals=["Mental escape for 10 mins"],
            preferred_channels=[Channel.word_of_mouth],
            cognitive_biases=["present bias"],
            current_tools=["Instagram", "YouTube"],
            switching_cost_tolerance=3,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=4,
            network_influence=5,
            bio="Might be the exact target audience, but prefers watching YouTube for free."
        ),
        SimulatedAgentProfile(
            agent_id="agent_10",
            name="Kevin",
            age=25,
            gender="Male",
            location="San Francisco, CA",
            occupation="Tech Support",
            annual_income_usd=55000.0,
            archetype=Archetype.skeptic,
            willingness_to_pay_usd=0.0,
            tech_savviness=9,
            pain_points=[PainPoint(topic="Battery drain on phone", intensity=7)],
            goals=["Save money"],
            preferred_channels=[Channel.social_media],
            cognitive_biases=["belief bias"],
            current_tools=["Reddit", "Twitch"],
            switching_cost_tolerance=2,
            decision_authority=DecisionAuthority.individual,
            purchase_urgency=1,
            network_influence=6,
            bio="Reads extensively about why Quibi is a bad idea on Reddit."
        )
    ]
    
    state: SimulationState = {
        "product": product,
        "personas": agents,
        "interactions": [],
        "error": None
    }
    
    return state

def run_simulation():
    print("Executing Quibi Launch Simulation with 10 GenZ/Millennial Personas...")
    print("==================================================")
    state = create_quibi_data()
    
    result = launcher_node(state)
    
    interactions = result.get("interactions", [])
    
    interaction_counts = {}
    purchase_count = 0
    
    for interaction in interactions:
        itype = interaction.interaction_type.value
        interaction_counts[itype] = interaction_counts.get(itype, 0) + 1
        if itype == "purchased":
            purchase_count += 1
            
    print("Interaction Summary:")
    print("-" * 30)
    for itype, count in sorted(interaction_counts.items()):
        percentage = (count / len(interactions)) * 100
        print(f"{itype.capitalize():<12}: {count:>2} agents ({percentage:>5.1f}%)")
    
    print()
    print("----- Agent Reasoning / Objections -----")
    for idx, interaction in enumerate(interactions):
        print(f"Agent {interaction.agent_id} [{interaction.interaction_type.value.upper()}]: {interaction.reasoning}")
        
    print()
    print(f"Total purchases: {purchase_count}/{len(interactions)}")
    print("✅ Simulation complete!")

if __name__ == "__main__":
    run_simulation()
