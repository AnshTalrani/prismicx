"""
Niche Vector Store Service implementation.
Provides methods for managing and querying niche-specific vector stores.
"""

import os
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

from pymongo.database import Database
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from models.vector_store import (
    NicheDocument, NicheDocuments, NicheMetadata, NicheStoreRequest,
    QueryRequest, QueryResult, StoreInfo, DocumentMetadata
)

logger = logging.getLogger("niche-vector-service")

# Base directory for storing niche vector databases
NICHE_VECTOR_STORE_DIR = os.getenv("NICHE_VECTOR_STORE_DIR", "./data/niche_vector_stores")

class NicheVectorService:
    """
    Provides vector store operations for niche-specific document storage and retrieval.
    """
    
    def __init__(self, db: Database):
        """
        Initialize the niche vector store service.
        
        Args:
            db: MongoDB database connection
        """
        self.db = db
        
        # Collections for storing metadata
        self.niches_collection = self.db["niches"]
        self.niche_documents_collection = self.db["niche_documents"]
        
        # Ensure indexes
        self._ensure_indexes()
        
        # Initialize embedding model
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            path=NICHE_VECTOR_STORE_DIR,
            prefer_grpc=True
        )
        
        # For keyword search (BM25)
        self.bm25_corpus = {}
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        
    def _ensure_indexes(self):
        """Ensure required indexes exist in the database."""
        # Indexes for niches collection
        self.niches_collection.create_index("name", unique=True)
        self.niches_collection.create_index("parent_niche")
        self.niches_collection.create_index("bot_types")
        self.niches_collection.create_index("tags")
        
        # Indexes for niche documents collection
        self.niche_documents_collection.create_index("id", unique=True)
        self.niche_documents_collection.create_index("niche")
        self.niche_documents_collection.create_index("sub_niche")
        self.niche_documents_collection.create_index([
            ("niche", 1),
            ("metadata.tenant_id", 1)
        ])
        
    async def create_niche_store(self, request: NicheStoreRequest, tenant_id: str = "") -> Dict:
        """
        Create a new niche-specific vector store.
        
        Args:
            request: Store creation request
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            Metadata for the created store
        """
        # Check if store already exists
        existing = await self.niches_collection.find_one({"name": request.name})
        if existing:
            raise ValueError(f"Niche store with name '{request.name}' already exists")
            
        # Create collection in Qdrant
        self.qdrant_client.recreate_collection(
            collection_name=request.name,
            vectors_config=qdrant_models.VectorParams(
                size=384,  # Dimension for all-MiniLM-L6-v2
                distance=qdrant_models.Distance.COSINE
            )
        )
        
        # Store niche metadata
        for niche in request.niches:
            await self.niches_collection.insert_one({
                "store_name": request.name,
                "name": niche.name,
                "description": niche.description,
                "parent_niche": niche.parent_niche,
                "keywords": niche.keywords,
                "tags": niche.tags,
                "bot_types": niche.bot_types,
                "created_at": datetime.utcnow(),
                "tenant_id": tenant_id
            })
            
        # Initialize BM25 corpus for this collection
        self.bm25_corpus[request.name] = {}
            
        logger.info(f"Created niche vector store: {request.name} with {len(request.niches)} niches")
        
        return {
            "name": request.name,
            "niches": len(request.niches),
            "description": request.description
        }
    
    async def list_niches(self, store_name: Optional[str] = None, tenant_id: str = "") -> List[Dict]:
        """
        List all available niches.
        
        Args:
            store_name: Optional store name to filter by
            tenant_id: Optional tenant ID filter
            
        Returns:
            List of niches
        """
        query = {"tenant_id": tenant_id} if tenant_id else {}
        if store_name:
            query["store_name"] = store_name
        
        niches = []
        async for niche in self.niches_collection.find(query):
            # Remove internal fields
            niche.pop("_id", None)
            niches.append(niche)
            
        return niches
        
    async def add_niche_documents(self, store_name: str, documents: List[NicheDocument], tenant_id: str = "") -> List[str]:
        """
        Add documents to a niche vector store.
        
        Args:
            store_name: Name of the store
            documents: List of documents to add
            tenant_id: Optional tenant ID
            
        Returns:
            List of document IDs
        """
        # Check if store exists
        niche_count = await self.niches_collection.count_documents({"store_name": store_name})
        if niche_count == 0:
            raise ValueError(f"Niche store '{store_name}' not found")
            
        # Prepare documents for insertion
        texts = []
        metadatas = []
        ids = []
        
        # Also prepare documents for MongoDB storage and BM25 indexing
        mongo_docs = []
        bm25_docs = []
        
        for doc in documents:
            # Generate an ID if not provided
            doc_id = str(uuid.uuid4()) if not doc.metadata.additional_metadata.get("id") else doc.metadata.additional_metadata.get("id")
            
            # Add tenant ID to metadata
            doc.metadata.tenant_id = tenant_id
            
            # Prepare document for vector storage
            texts.append(doc.text)
            
            # Add niche information to metadata
            metadata = doc.metadata.dict()
            metadata["niche"] = doc.niche
            if doc.sub_niche:
                metadata["sub_niche"] = doc.sub_niche
                
            metadatas.append(metadata)
            ids.append(doc_id)
            
            # Prepare for MongoDB
            mongo_docs.append({
                "id": doc_id,
                "store_name": store_name,
                "niche": doc.niche,
                "sub_niche": doc.sub_niche,
                "text": doc.text,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
                "tenant_id": tenant_id
            })
            
            # Add to BM25 corpus
            bm25_docs.append(doc.text)
            
        # Store in Qdrant
        embeddings = self.embedding_model.embed_documents(texts)
        
        # Convert documents to Qdrant points
        points = []
        for i, (doc_id, embedding, metadata) in enumerate(zip(ids, embeddings, metadatas)):
            points.append(
                qdrant_models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=metadata
                )
            )
            
        # Upload in batches
        self.qdrant_client.upsert(
            collection_name=store_name,
            points=points
        )
        
        # Store in MongoDB
        if mongo_docs:
            await self.niche_documents_collection.insert_many(mongo_docs)
            
        # Update BM25 index for this collection
        if store_name in self.bm25_corpus:
            if doc.niche not in self.bm25_corpus[store_name]:
                self.bm25_corpus[store_name][doc.niche] = []
                
            self.bm25_corpus[store_name][doc.niche].extend(bm25_docs)
            
        logger.info(f"Added {len(documents)} documents to niche store '{store_name}'")
        return ids
        
    async def search_niche(
        self,
        query: QueryRequest,
        niche: Optional[str] = None,
        sub_niche: Optional[str] = None,
        tenant_id: str = ""
    ) -> List[QueryResult]:
        """
        Search for documents in a niche vector store.
        
        Args:
            query: Search query
            niche: Optional niche to search within
            sub_niche: Optional sub-niche to search within
            tenant_id: Optional tenant ID
            
        Returns:
            List of search results
        """
        collection_name = query.collection_name
        
        # Create filter for Qdrant
        qdrant_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="tenant_id",
                    match=qdrant_models.MatchValue(value=tenant_id)
                )
            ]
        )
        
        # Add niche filter if provided
        if niche:
            qdrant_filter.must.append(
                qdrant_models.FieldCondition(
                    key="niche",
                    match=qdrant_models.MatchValue(value=niche)
                )
            )
            
        # Add sub-niche filter if provided
        if sub_niche:
            qdrant_filter.must.append(
                qdrant_models.FieldCondition(
                    key="sub_niche",
                    match=qdrant_models.MatchValue(value=sub_niche)
                )
            )
            
        # Add any additional filters from the query
        if query.filter_metadata:
            for key, value in query.filter_metadata.items():
                if key not in ["niche", "sub_niche", "tenant_id"]:
                    qdrant_filter.must.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value)
                        )
                    )
                    
        # Perform vector search
        query_embedding = self.embedding_model.embed_query(query.text)
        vector_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=query.top_k,
            query_filter=qdrant_filter
        )
        
        # If not using hybrid search, return vector results directly
        if not query.hybrid_search:
            return [
                QueryResult(
                    id=str(result.id),
                    text=result.payload.get("text", ""),
                    metadata=DocumentMetadata(**result.payload),
                    similarity_score=result.score
                )
                for result in vector_results
            ]
            
        # If using hybrid search, combine with keyword search
        # Get all documents for the requested niche
        filter_query = {"store_name": collection_name, "tenant_id": tenant_id}
        if niche:
            filter_query["niche"] = niche
        if sub_niche:
            filter_query["sub_niche"] = sub_niche
            
        # Get documents from MongoDB to perform keyword search
        mongo_docs = []
        async for doc in self.niche_documents_collection.find(filter_query):
            mongo_docs.append(doc)
            
        # Perform keyword search using TF-IDF
        if mongo_docs:
            texts = [doc["text"] for doc in mongo_docs]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            query_vec = self.tfidf_vectorizer.transform([query.text])
            
            # Calculate cosine similarity
            keyword_scores = (tfidf_matrix @ query_vec.T).toarray().flatten()
            
            # Create mapping from doc_id to keyword score
            keyword_score_map = {
                doc["id"]: score
                for doc, score in zip(mongo_docs, keyword_scores)
            }
            
            # Blend vector and keyword scores
            results = []
            for result in vector_results:
                doc_id = str(result.id)
                vector_score = result.score
                keyword_score = keyword_score_map.get(doc_id, 0.0)
                
                # Weighted combination
                combined_score = (1 - query.keyword_weight) * vector_score + query.keyword_weight * keyword_score
                
                results.append(
                    QueryResult(
                        id=doc_id,
                        text=result.payload.get("text", ""),
                        metadata=DocumentMetadata(**result.payload),
                        similarity_score=combined_score
                    )
                )
                
            # Re-sort based on combined score
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Limit to top_k
            return results[:query.top_k]
        
        # Fallback to vector search results if no keyword search possible
        return [
            QueryResult(
                id=str(result.id),
                text=result.payload.get("text", ""),
                metadata=DocumentMetadata(**result.payload),
                similarity_score=result.score
            )
            for result in vector_results
        ]
        
    async def delete_niche_documents(
        self,
        store_name: str,
        niche: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        filter_metadata: Optional[Dict] = None,
        tenant_id: str = ""
    ) -> int:
        """
        Delete documents from a niche vector store.
        
        Args:
            store_name: Name of the store
            niche: Optional niche to delete from
            document_ids: Optional list of document IDs to delete
            filter_metadata: Optional metadata filter
            tenant_id: Optional tenant ID
            
        Returns:
            Number of documents deleted
        """
        # Build MongoDB filter
        filter_dict = {"store_name": store_name, "tenant_id": tenant_id}
        if niche:
            filter_dict["niche"] = niche
            
        # Add other metadata filters
        if filter_metadata:
            for key, value in filter_metadata.items():
                filter_dict[f"metadata.{key}"] = value
                
        # Get document IDs if not provided
        if not document_ids:
            ids_to_delete = []
            async for doc in self.niche_documents_collection.find(filter_dict, {"id": 1}):
                ids_to_delete.append(doc["id"])
        else:
            ids_to_delete = document_ids
            filter_dict["id"] = {"$in": ids_to_delete}
            
        # Delete from Qdrant
        if ids_to_delete:
            self.qdrant_client.delete(
                collection_name=store_name,
                points_selector=qdrant_models.PointIdsList(
                    points=ids_to_delete
                )
            )
            
            # Delete from MongoDB
            result = await self.niche_documents_collection.delete_many(filter_dict)
            
            return result.deleted_count
            
        return 0 