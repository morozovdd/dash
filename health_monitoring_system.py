from uagents import Bureau
import os

# Set environment variables
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN")
os.environ["USER_CHAT_ID"] = os.getenv("USER_CHAT_ID")
os.environ["EMERGENCY_CONTACT_CHAT_ID"] = os.getenv("EMERGENCY_CONTACT_CHAT_ID")

# Create and configure Bureau
bureau = Bureau(
    port=8000,
    endpoint="http://localhost:8000/submit"
)

from collector_agent import collector_agent
from analyzer_agent import analyzer_agent
from decision_maker import decision_maker
from locator_agent import locator_agent

# Add agents to bureau
bureau.add(collector_agent)
bureau.add(analyzer_agent)
bureau.add(decision_maker)
bureau.add(locator_agent)

os.environ['ANALYZER_ADDRESS'] = analyzer_agent.address
os.environ['COLLECTOR_ADDRESS'] = collector_agent.address
os.environ['DECISION_MAKER_ADDRESS'] = decision_maker.address

print(f"Analyzer address: {analyzer_agent.address}")
print(f"Decision maker address: {decision_maker.address}")
print(f"Collector address: {collector_agent.address}")

if __name__ == "__main__":
    bureau.run()