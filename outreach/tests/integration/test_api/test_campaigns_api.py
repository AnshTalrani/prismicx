import pytest
from fastapi.testclient import TestClient
from uuid import UUID
import sys
import os

import_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src/api'))
if import_path not in sys.path:
    sys.path.insert(0, import_path)

from minimal_app import app

def test_create_and_list_campaigns():
    with TestClient(app) as client:
        # Create a campaign
        resp = client.post("/campaigns", json={"name": "API Test Campaign", "status": "draft"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "API Test Campaign"
        assert data["status"] == "draft"
        assert UUID(data["id"])

        # List campaigns
        resp2 = client.get("/campaigns")
        assert resp2.status_code == 200
        campaigns = resp2.json()
        assert any(c["id"] == data["id"] for c in campaigns)
