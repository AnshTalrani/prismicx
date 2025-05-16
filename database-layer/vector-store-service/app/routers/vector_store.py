"""
Vector Store API Routes
----------------------

This module provides REST API endpoints for managing vector stores.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional, Any
from pymongo.database import Database

from dependencies import get_tenant_mongodb, get_validated_tenant_id
from models.vector_store import (
    Document, Documents, StoreRequest, QueryRequest, 
    QueryResponse, StoreInfo, StoreListResponse, DeleteRequest
)
from services.vector_store_service import VectorStoreService

router = APIRouter()

def get_vector_store_service(db: Database = Depends(get_tenant_mongodb)) -> VectorStoreService:
    """Get vector store service instance with tenant database."""
    return VectorStoreService(db)

@router.post("/stores", status_code=status.HTTP_201_CREATED)
async def create_store(
    request: StoreRequest,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Create a new vector store.
    
    A vector store is a collection of documents with vector embeddings.
    Each store uses a specific embedding model and vector database backend.
    """
    try:
        metadata = await service.create_store(request, tenant_id)
        return {
            "status": "success",
            "message": f"Vector store '{request.name}' created successfully",
            "metadata": metadata
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vector store: {str(e)}"
        )

@router.get("/stores", response_model=StoreListResponse)
async def list_stores(
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    List all available vector stores.
    
    Returns a list of all vector stores available to the current tenant.
    """
    try:
        stores = await service.list_stores(tenant_id)
        return {"stores": stores}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vector stores: {str(e)}"
        )

@router.get("/stores/{collection_name}", response_model=StoreInfo)
async def get_store_info(
    collection_name: str,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Get information about a specific vector store.
    
    Returns detailed information about a specific vector store,
    including metadata and document count.
    """
    try:
        store_info = await service.get_store_info(collection_name, tenant_id)
        return store_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get store info: {str(e)}"
        )

@router.post("/stores/{collection_name}/documents")
async def add_documents(
    collection_name: str,
    documents: Documents,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Add documents to a vector store.
    
    Documents will be embedded and stored in the vector store.
    Returns the IDs of the added documents.
    """
    try:
        ids = await service.add_documents(collection_name, documents.documents, tenant_id)
        return {
            "status": "success",
            "message": f"Added {len(ids)} documents to {collection_name}",
            "document_ids": ids
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents: {str(e)}"
        )

@router.post("/search", response_model=QueryResponse)
async def search_documents(
    query: QueryRequest,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Search for similar documents in a vector store.
    
    Performs a semantic search to find documents similar to the query text.
    Returns a list of documents with similarity scores.
    """
    try:
        results = await service.search(query, tenant_id)
        return QueryResponse(
            results=results,
            query=query.text,
            collection_name=query.collection_name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}"
        )

@router.delete("/stores/{collection_name}/documents")
async def delete_documents(
    collection_name: str,
    request: DeleteRequest,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Delete documents from a vector store.
    
    Documents can be deleted by ID or by metadata filter.
    Returns the number of documents deleted.
    """
    try:
        count = await service.delete_documents(
            collection_name,
            request.document_ids,
            request.filter_metadata,
            tenant_id
        )
        return {
            "status": "success",
            "message": f"Deleted {count} documents from {collection_name}",
            "deleted_count": count
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        ) 