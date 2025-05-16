"""
Data models for vector store operations.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class VectorStoreType(str, Enum):
    """The type of vector store to use."""
    FAISS = "faiss"
    CHROMA = "chroma"
    PINECONE = "pinecone"  # For future implementation
    QDRANT = "qdrant"  # Added for efficient niche-based filtering

class EmbeddingModelType(str, Enum):
    """The type of embedding model to use."""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"

class StoreMetadata(BaseModel):
    """Metadata about a vector store."""
    name: str
    description: Optional[str] = None
    bot_type: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    vector_count: int = 0
    embedding_dim: int = 0
    store_type: VectorStoreType = VectorStoreType.CHROMA
    embedding_model: EmbeddingModelType = EmbeddingModelType.SENTENCE_TRANSFORMERS
    model_name: Optional[str] = "all-MiniLM-L6-v2"  # Default model

class DocumentMetadata(BaseModel):
    """Metadata for a document stored in the vector store."""
    source: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    content_type: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    tenant_id: Optional[str] = None
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    """A document to be stored in the vector store."""
    text: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    id: Optional[str] = None

class Documents(BaseModel):
    """A list of documents to be stored in the vector store."""
    documents: List[Document]

class StoreRequest(BaseModel):
    """Request to create a new vector store."""
    name: str
    description: Optional[str] = None
    bot_type: Optional[str] = None
    domain: Optional[str] = None
    store_type: VectorStoreType = VectorStoreType.CHROMA
    embedding_model: EmbeddingModelType = EmbeddingModelType.SENTENCE_TRANSFORMERS
    model_name: Optional[str] = "all-MiniLM-L6-v2"  # Default model
    tags: List[str] = Field(default_factory=list)

class QueryRequest(BaseModel):
    """Request to query a vector store."""
    text: str
    collection_name: str
    filter_metadata: Optional[Dict[str, Any]] = None
    top_k: int = 5
    similarity_threshold: Optional[float] = 0.7
    hybrid_search: bool = False  # Added for hybrid search capabilities
    keyword_weight: float = 0.3  # Weighting factor for hybrid search

class QueryResult(BaseModel):
    """Result of a query to a vector store."""
    text: str
    metadata: DocumentMetadata
    id: str
    similarity_score: float

class QueryResponse(BaseModel):
    """Response from a query to a vector store."""
    results: List[QueryResult]
    query: str
    collection_name: str

class StoreInfo(BaseModel):
    """Information about a store."""
    name: str
    metadata: StoreMetadata
    document_count: int

class StoreListResponse(BaseModel):
    """Response listing all available stores."""
    stores: List[StoreInfo]

class DeleteRequest(BaseModel):
    """Request to delete documents from a vector store."""
    collection_name: str
    document_ids: Optional[List[str]] = None
    filter_metadata: Optional[Dict[str, Any]] = None

# New models for niche-specific functionality

class NicheMetadata(BaseModel):
    """Metadata for a specific niche."""
    name: str
    description: Optional[str] = None
    parent_niche: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    bot_types: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class NicheDocument(BaseModel):
    """A document with niche-specific metadata."""
    text: str
    niche: str
    sub_niche: Optional[str] = None
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    
class NicheDocuments(BaseModel):
    """A collection of niche-specific documents."""
    documents: List[NicheDocument]
    
class NicheStoreRequest(BaseModel):
    """Request to create a new niche-specific store."""
    name: str
    description: Optional[str] = None
    niches: List[NicheMetadata]
    store_type: VectorStoreType = VectorStoreType.QDRANT  # Default to Qdrant for niche stores
    embedding_model: EmbeddingModelType = EmbeddingModelType.SENTENCE_TRANSFORMERS
    model_name: Optional[str] = "all-MiniLM-L6-v2" 