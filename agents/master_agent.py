import asyncio
import logging
from datetime import datetime, timezone
import uuid

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
    EndSessionContent,
    chat_protocol_spec
)

from backend.config import settings
from backend.orchestrator import CommandOrchestrator
from services.intent_service import IntentParserService
from services.storage_service import storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reliefmesh.agent")

# Initialize the public Fetch.ai uAgent
mailbox_config = settings.AGENT_MAILBOX_KEY if settings.AGENT_MAILBOX_KEY else False

agent = Agent(
    name=settings.AGENT_NAME,
    seed=settings.AGENT_SEED,
    port=settings.AGENT_PORT,
    endpoint=[settings.AGENT_ENDPOINT],
    mailbox=mailbox_config
)

# Instantiate the standard Fetch.ai Agent Chat Protocol (ACP)
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handles incoming ChatMessage conforming to the ASI:One Agent Chat Protocol.
    1. Immediately acknowledges receipt via ChatAcknowledgement.
    2. Extracts user text content.
    3. Runs IntentParser + CommandOrchestrator.
    4. Responds with structured, explainable emergency allocation report.
    """
    ctx.logger.info(f"Received ACP ChatMessage from {sender} (msg_id={msg.msg_id})")

    # 1. Immediate receipt acknowledgement (mandatory for ACP & ASI:One responsiveness)
    try:
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        )
        await ctx.send(sender, ack)
        ctx.logger.info(f"Sent ChatAcknowledgement for msg_id={msg.msg_id}")
    except Exception as e:
        ctx.logger.warning(f"Could not send ChatAcknowledgement: {e}")

    # 2. Extract incoming text
    user_prompt = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_prompt += item.text + " "

    user_prompt = user_prompt.strip()
    ctx.logger.info(f"Processing user prompt: '{user_prompt}'")

    if not user_prompt:
        reply_text = (
            "ReliefMesh Autonomous Emergency Coordinator online.\n"
            "Please describe a simulated disaster scenario or specify supply constraints.\n"
            "Example: 'Simulate flood relief for North Zone and River Zone with 500 food kits and 300 water units.'"
        )
        response_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid.uuid4(),
            content=[TextContent(type="text", text=reply_text)]
        )
        await ctx.send(sender, response_msg)
        return

    # 3. Intent parsing & execution
    parsed, provider_name = await IntentParserService.parse_prompt(user_prompt)

    if parsed.get("action") == "reset":
        storage_service.reset_to_demo()
        reply_text = (
            "**[ReliefMesh State Reset]**\n\n"
            "Demo dataset and warehouse inventory have been successfully restored to default baseline.\n"
            "Ready for new emergency coordination queries."
        )
    elif parsed.get("action") == "status":
        inv = storage_service.get_current_inventory()
        inv_lines = [f"- **{k.replace('_', ' ').title()}:** {v.available_quantity} {v.unit} available" for k, v in inv.items()]
        reply_text = (
            f"**[ReliefMesh Central Depot Inventory Status]**\n"
            f"*Provider: {provider_name}*\n\n" + "\n".join(inv_lines)
        )
    else:
        # Run full multi-agent coordination simulation
        scen = storage_service.get_scenario()
        if not scen:
            scen = storage_service.reset_to_demo()

        # Apply parsed inventory overrides if any were detected in prompt
        custom_inv = {k: v.model_copy(deep=True) for k, v in scen.inventory.items()}
        overrides = parsed.get("inventory_overrides", {})
        for res_name, qty in overrides.items():
            if res_name in custom_inv:
                custom_inv[res_name].total_initial_quantity = qty
                custom_inv[res_name].available_quantity = qty

        report = await CommandOrchestrator.run_simulation(
            scenario=scen,
            custom_inventory=custom_inv if overrides else None
        )

        trace_summary = ", ".join(f"{ev.agent_name}:{ev.action}" for ev in report.execution_trace[:5])

        reply_text = (
            f"**[ReliefMesh Coordination Result]**\n"
            f"**Intent Source:** {provider_name}\n"
            f"**Execution Trace:** {trace_summary}...\n\n"
            f"{report.human_readable_summary}"
        )

    # 4. Return ACP response message
    response_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text=reply_text)]
    )
    await ctx.send(sender, response_msg)
    ctx.logger.info(f"Dispatched coordination response to {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """
    Handles incoming acknowledgements confirming that the recipient received our response.
    """
    ctx.logger.info(f"Received ChatAcknowledgement from {sender} for msg_id={msg.acknowledged_msg_id}")

# Include chat protocol in agent with manifest publishing enabled
agent.include(chat_proto, publish_manifest=True)

@agent.on_event("startup")
async def startup_banner(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"ReliefMesh uAgent started!")
    ctx.logger.info(f"Agent Name:    {agent.name}")
    ctx.logger.info(f"Agent Address: {agent.address}")
    ctx.logger.info(f"Agent Port:    {settings.AGENT_PORT}")
    ctx.logger.info(f"Mailbox Active: {'YES' if settings.AGENT_MAILBOX_KEY else 'NO (Local Direct Mode)'}")
    ctx.logger.info("=" * 60)

if __name__ == "__main__":
    agent.run()
