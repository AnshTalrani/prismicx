import pytest
from fastapi.testclient import TestClient
from uuid import uuid4, UUID
import sys
import os

import_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/api'))
if import_path not in sys.path:
    sys.path.insert(0, import_path)

from minimal_app import app

def test_create_and_list_conversations():
    with TestClient(app) as client:
        # Create a campaign first (required for conversation)
        resp = client.post("/campaigns", json={"name": "For Conversation", "status": "active"})
        assert resp.status_code == 200
        campaign = resp.json()
        campaign_id = campaign["id"]
        contact_id = str(uuid4())

        # Start a conversation
        resp2 = client.post("/conversations", json={"campaign_id": campaign_id, "contact_id": contact_id, "context": {"foo": "bar"}})
        assert resp2.status_code == 200
        conv = resp2.json()
        assert conv["campaign_id"] == campaign_id
        assert conv["contact_id"] == contact_id
        assert UUID(conv["id"])
        assert conv["context"] == {"foo": "bar"}

        # List conversations
        resp3 = client.get("/conversations")
        assert resp3.status_code == 200
        conversations = resp3.json()
        assert any(c["id"] == conv["id"] for c in conversations)
