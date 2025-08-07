"""
Repository Layer

This package contains repository classes that abstract database access,
providing a clean interface between the database and service layers.
"""

# Export public API
__all__ = [
    'BaseRepository',
    'CampaignRepository',
    'ContactRepository',
    'ConversationRepository',
    'MessageRepository',
    'WorkflowRepository'
]
