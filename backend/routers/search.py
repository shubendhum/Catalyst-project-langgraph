"""
Search API Router
Hybrid RAG search endpoint
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from services.rag_service import get_retriever

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query")
    project: Optional[str] = Field(None, description="Filter by project")
    sprint: Optional[str] = Field(None, description="Filter by sprint")
    since_days: Optional[int] = Field(None, description="Only search items from last N days", ge=1)
    top_k: int = Field(10, description="Number of results to return", ge=1, le=100)
    use_hybrid: bool = Field(True, description="Use hybrid search (BM25 + vector). If False, vector only.")


class SearchResult(BaseModel):
    """Search result model"""
    doc_id: str
    text: str
    source: str
    title: str
    url: Optional[str] = None
    owner: Optional[str] = None
    project: Optional[str] = None
    sprint: Optional[str] = None
    tags: List[str] = []
    score: float
    fused_score: Optional[float] = None
    retrieval_method: str


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    total_results: int
    filters_applied: Dict[str, Any]


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Hybrid RAG search endpoint
    
    Combines BM25 (keyword) and vector (semantic) search with score fusion.
    Returns results with source attribution and metadata.
    
    Example:
        POST /api/search
        {
            "query": "How to deploy to production?",
            "project": "CATALYST",
            "since_days": 30,
            "top_k": 5
        }
    
    Returns:
        {
            "query": "How to deploy to production?",
            "results": [
                {
                    "text": "Production deployment guide...",
                    "source": "confluence",
                    "title": "Deployment Guide",
                    "url": "https://confluence.company.com/...",
                    "score": 0.95,
                    "fused_score": 0.042
                }
            ],
            "total_results": 5
        }
    """
    try:
        # Get retriever
        retriever = get_retriever()
        
        # Perform search
        results = await retriever.search(
            query=request.query,
            top_k=request.top_k,
            project=request.project,
            sprint=request.sprint,
            since_days=request.since_days,
            use_hybrid=request.use_hybrid
        )
        
        # Format response
        filters_applied = {}
        if request.project:
            filters_applied['project'] = request.project
        if request.sprint:
            filters_applied['sprint'] = request.sprint
        if request.since_days:
            filters_applied['since_days'] = request.since_days
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/sources")
async def get_available_sources():
    """
    Get list of available document sources
    
    Returns available sources, projects, and sprints for filtering.
    """
    try:
        retriever = get_retriever()
        
        # Query unique sources from BM25 index
        cursor = retriever.bm25_retriever.conn.cursor()
        
        # Get unique sources
        cursor.execute("SELECT DISTINCT source FROM documents_meta WHERE source != ''")
        sources = [row[0] for row in cursor.fetchall()]
        
        # Get unique projects
        cursor.execute("SELECT DISTINCT project FROM documents_meta WHERE project != ''")
        projects = [row[0] for row in cursor.fetchall()]
        
        # Get unique sprints
        cursor.execute("SELECT DISTINCT sprint FROM documents_meta WHERE sprint != ''")
        sprints = [row[0] for row in cursor.fetchall()]
        
        # Get document counts
        cursor.execute("SELECT COUNT(*) FROM documents_meta")
        total_docs = cursor.fetchone()[0]
        
        cursor.execute("SELECT source, COUNT(*) FROM documents_meta GROUP BY source")
        source_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_documents": total_docs,
            "sources": sources,
            "projects": projects,
            "sprints": sprints,
            "source_counts": source_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sources: {str(e)}"
        )


@router.delete("/cache")
async def clear_cache():
    """
    Clear search cache and reinitialize retrievers
    
    Use this after ingesting new documents.
    """
    try:
        global _retriever
        from services.rag_service import _retriever
        
        if _retriever:
            _retriever.close()
            _retriever = None
        
        return {"message": "Search cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
