"""
Niche Vector Store API Routes
----------------------------

This module provides REST API endpoints for managing niche-specific vector stores.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional, Any
from pymongo.database import Database

from dependencies import get_tenant_mongodb, get_validated_tenant_id
from models.vector_store import (
    NicheDocument, NicheDocuments, NicheMetadata, NicheStoreRequest,
    QueryRequest, QueryResponse, QueryResult
)
from services.niche_vector_service import NicheVectorService

router = APIRouter()

def get_niche_vector_service(db: Database = Depends(get_tenant_mongodb)) -> NicheVectorService:
    """Get niche vector service instance with tenant database."""
    return NicheVectorService(db)

@router.post("/stores", status_code=status.HTTP_201_CREATED)
async def create_niche_store(
    request: NicheStoreRequest,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: NicheVectorService = Depends(get_niche_vector_service)
):
    """
    Create a new niche-specific vector store.
    
    A niche store is organized into categories and subcategories of niche data.
    Each store contains a collection of niches and allows efficient retrieval
    of documents within those niches.
    """
    try:
        metadata = await service.create_niche_store(request, tenant_id)
        return {
            "status": "success",
            "message": f"Niche vector store '{request.name}' created successfully",
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
            detail=f"Failed to create niche store: {str(e)}"
        )

@router.get("/niches")
async def list_niches(
    store_name: Optional[str] = None,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: NicheVectorService = Depends(get_niche_vector_service)
):
    """
    List all available niches.
    
    Returns a list of all niches available to the current tenant.
    Optionally filter by store name.
    """
    try:
        niches = await service.list_niches(store_name, tenant_id)
        return {"niches": niches, "count": len(niches)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list niches: {str(e)}"
        )

@router.post("/stores/{store_name}/documents")
async def add_niche_documents(
    store_name: str,
    documents: NicheDocuments,
    tenant_id: str = Depends(get_validated_tenant_id),
    service: NicheVectorService = Depends(get_niche_vector_service)
):
    """
    Add documents to a niche vector store.
    
    Documents will be added to their respective niches and sub-niches.
    Returns the IDs of the added documents.
    """
    try:
        ids = await service.add_niche_documents(store_name, documents.documents, tenant_id)
        return {
            "status": "success",
            "message": f"Added {len(ids)} documents to niche store '{store_name}'",
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

@router.post("/search/{store_name}")
async def search_niche(
    store_name: str,
    query: QueryRequest,
    niche: Optional[str] = Query(None, description="Niche to search within"),
    sub_niche: Optional[str] = Query(None, description="Sub-niche to search within"),
    tenant_id: str = Depends(get_validated_tenant_id),
    service: NicheVectorService = Depends(get_niche_vector_service)
):
    """
    Search for documents in a niche vector store.
    
    Performs a semantic search to find documents similar to the query text
    within the specified niche and sub-niche. If hybrid_search is enabled,
    combines vector similarity with keyword relevance.
    
    Returns a list of documents with similarity scores.
    """
    try:
        # Override collection name with the store name from the path
        query.collection_name = store_name
        
        results = await service.search_niche(query, niche, sub_niche, tenant_id)
        return QueryResponse(
            results=results,
            query=query.text,
            collection_name=store_name
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

@router.delete("/stores/{store_name}/documents")
async def delete_niche_documents(
    store_name: str,
    niche: Optional[str] = Query(None, description="Niche to delete from"),
    document_ids: Optional[List[str]] = Query(None, description="IDs of documents to delete"),
    tenant_id: str = Depends(get_validated_tenant_id),
    service: NicheVectorService = Depends(get_niche_vector_service)
):
    """
    Delete documents from a niche vector store.
    
    Documents can be deleted by ID or by niche.
    Returns the number of documents deleted.
    """
    try:
        count = await service.delete_niche_documents(
            store_name,
            niche,
            document_ids,
            None,  # No filter metadata for this endpoint
            tenant_id
        )
        return {
            "status": "success",
            "message": f"Deleted {count} documents from niche store '{store_name}'",
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