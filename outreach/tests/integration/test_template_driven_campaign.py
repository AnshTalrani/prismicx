import pytest
import asyncio
from uuid import uuid4
from src.core.campaign_manager import CampaignManager
from src.services.campaign_service import CampaignService
from src.services.conversation_service import ConversationService
from src.services.workflow_service import WorkflowService
from src.services.notification_service import NotificationService
from src.services.stt_service import STTService
from src.services.llm_service import LLMService
from src.services.tts_service import TTSService
from src.config.template_loader import load_campaign_template
from src.models.contact import Contact, ContactList

class DummySTT(STTService):
    async def transcribe(self, audio_bytes: bytes) -> str:
        return "transcribed audio"

class DummyLLM(LLMService):
    async def generate_response(self, context: dict, prompt: str) -> str:
        return f"AI response to: {prompt}"

class DummyTTS(TTSService):
    async def synthesize(self, text: str) -> bytes:
        return b"audio-bytes"

@pytest.mark.asyncio
async def test_template_driven_campaign(monkeypatch):
    # Setup dummy services and repositories (use in-memory or mocks)
    class DummyRepo:
        def __init__(self):
            self.data = {}
        async def create(self, obj):
            self.data[obj.id] = obj
            return obj
        async def get(self, obj_id):
            return self.data.get(obj_id)
        async def update(self, obj_id, update_data):
            obj = self.data.get(obj_id)
            for k, v in update_data.items():
                setattr(obj, k, v)
            return obj
        async def list(self, filters):
            return list(self.data.values())
        async def add_message(self, conv_id, msg):
            return msg
    
    campaign_repo = DummyRepo()
    conversation_repo = DummyRepo()
    workflow_repo = DummyRepo()
    notification_service = NotificationService()
    stt = DummySTT()
    llm = DummyLLM()
    tts = DummyTTS()

    # Patch NotificationService to avoid real notifications
    monkeypatch.setattr(notification_service, "send_campaign_notification", lambda *a, **kw: asyncio.sleep(0))

    campaign_service = CampaignService(campaign_repo)
    conversation_service = ConversationService(conversation_repo, stt, llm, tts)
    workflow_service = WorkflowService(workflow_repo)
    manager = CampaignManager(
        campaign_service,
        conversation_service,
        workflow_service,
        notification_service
    )

    # Prepare dummy campaign and workflow
    class DummyCampaign:
        def __init__(self, id, name, contact_list, workflow_id, status, type):
            self.id = id
            self.name = name
            self.contact_list = contact_list
            self.workflow_id = workflow_id
            self.status = status
            self.type = type
            self.settings = {}
            self.dict = lambda: self.__dict__
    class DummyWorkflow:
        def __init__(self, id):
            self.id = id
            self.steps = []
    campaign_id = uuid4()
    workflow_id = uuid4()
    contact_list = ContactList(contacts=[
        Contact(id="contact1", name="Alice"),
        Contact(id="contact2", name="Bob")
    ])
    campaign = DummyCampaign(
        id=campaign_id,
        name="Test Campaign",
        contact_list=contact_list,
        workflow_id=workflow_id,
        status="draft",
        type=type("CampaignType", (), {"value": "test"})
    )
    workflow = DummyWorkflow(workflow_id)
    await campaign_repo.create(campaign)
    await workflow_repo.create(workflow)

    # Run template-driven campaign
    started = await manager.start_campaign(campaign_id, template_name="campaign_template_example.json")
    assert started
    # Allow some time for async tasks to run
    await asyncio.sleep(0.2)
    # Check that contacts were processed (messages added, etc.)
    # (In a real test, check conversation_repo or logs for expected AI/ML output)
