import pytest
from datetime import datetime, timezone
import uuid
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent
)
from agents.master_agent import agent, chat_proto

def test_chat_protocol_structures():
    msg_id = uuid.uuid4()
    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=msg_id,
        content=[TextContent(type="text", text="Simulate flood relief for North Zone")]
    )

    assert msg.msg_id == msg_id
    assert len(msg.content) == 1
    assert msg.content[0].text == "Simulate flood relief for North Zone"

    # Immediate acknowledgement
    ack = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg.msg_id
    )
    assert ack.acknowledged_msg_id == msg_id

def test_protocol_verification_passed():
    # Ensure protocol spec passed internal verification and is correctly bound to agent
    assert chat_proto.verify() is True
    assert any(p.name == "AgentChatProtocol" for p in agent.protocols.values())
