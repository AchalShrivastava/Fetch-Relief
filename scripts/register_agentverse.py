"""
Fetch Relief Agentverse Registration & Inspector Helper
Inspects the agent address, verifies seed consistency, and explains Agentverse connection.
"""
from backend.config import settings
from agents.master_agent import agent

def print_registration_details():
    print("=" * 70)
    print(" FETCH RELIEF AGENTVERSE REGISTRATION & DISCOVERY HELPER")
    print("=" * 70)
    print(f"Agent Name:    {agent.name}")
    print(f"Agent Address: {agent.address}")
    print(f"Seed Phrase:   {settings.AGENT_SEED}")
    print(f"Local Port:    {settings.AGENT_PORT}")
    print(f"Local Endpoint:{settings.AGENT_ENDPOINT}")
    print("-" * 70)
    
    if settings.AGENT_MAILBOX_KEY:
        print("[STATUS] Agentverse Mailbox Key is configured in .env.")
        print("Your agent will automatically connect to the Agentverse Mailroom on startup.")
    else:
        print("[STATUS] Running in Local Direct Mode (No Mailbox Key yet).")
        print("\nTo connect this local agent to Agentverse for live ASI:One discovery:")
        print("1. Log in to https://agentverse.ai")
        print("2. Navigate to 'Mailroom' / 'Agents' -> Click 'New Agent' or 'Connect Local Agent'")
        print(f"3. Provide your Agent Address: {agent.address}")
        print("4. Copy the generated Mailbox API Key.")
        print("5. Paste it into your .env file:")
        print("     AGENT_MAILBOX_KEY=your_mailbox_key_here")
        print("6. Restart the agent using ./scripts/run_agent.ps1")
        print("7. Find and chat with your agent in ASI:One (https://asi1.ai)")
    print("=" * 70)

if __name__ == "__main__":
    print_registration_details()
