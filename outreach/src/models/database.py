"""
Database Models

This module contains SQLAlchemy models for the outreach system.
These models map to database tables and define the data schema.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship

# Base class for all database models
Base = declarative_base()

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class CampaignType(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    NURTURE = "nurture"
    SURVEY = "survey"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    SYSTEM = "system"

class MessageStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class Campaign(Base):
    """Campaign model representing an outreach campaign."""
    __tablename__ = "campaigns"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    campaign_type = Column(SQLEnum(CampaignType), nullable=False)
    workflow_id = Column(PG_UUID(as_uuid=True), ForeignKey('workflows.id'))
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    conversations = relationship("Conversation", back_populates="campaign")
    workflow = relationship("Workflow", back_populates="campaigns")

class Contact(Base):
    """Contact model representing a person to be contacted."""
    __tablename__ = "contacts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    conversations = relationship("Conversation", back_populates="contact")

class Conversation(Base):
    """Conversation model representing a series of messages with a contact."""
    __tablename__ = "conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(PG_UUID(as_uuid=True), ForeignKey('campaigns.id'))
    contact_id = Column(PG_UUID(as_uuid=True), ForeignKey('contacts.id'))
    status = Column(String(50), default="active")
    current_workflow_state = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    campaign = relationship("Campaign", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """Message model representing a single message in a conversation."""
    __tablename__ = "messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey('conversations.id'))
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.QUEUED)
    content_type = Column(String(50), default="text/plain")
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Workflow(Base):
    """Workflow model representing a conversation flow definition."""
    __tablename__ = "workflows"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=False)  # JSON definition of the workflow
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship("Campaign", back_populates="workflow")
