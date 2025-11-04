"""
RAG Retrieval Service
Hybrid retrieval combining BM25 and vector search with score fusion
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

logger = logging.getLogger(__name__)


class BM25Retriever:
    """BM25 full-text search using SQLite FTS5"""
    
    def __init__(self, db_path: str = "/app/data/bm25_index.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_database()
    
    def _init_database(self):
        """Initialize FTS5 table"""
        cursor = self.conn.cursor()
        
        # Create FTS5 virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(
                doc_id,
                text,
                source,
                title,
                metadata,
                tokenize='porter unicode61'
            )
        """)
        
        # Create regular table for metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents_meta (
                doc_id TEXT PRIMARY KEY,
                source TEXT,
                url TEXT,
                owner TEXT,
                project TEXT,
                sprint TEXT,
                tags TEXT,
                last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info("BM25 database initialized")
    
    def index_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """
        Index a document for BM25 search
        
        Args:
            doc_id: Unique document ID
            text: Document text
            metadata: Document metadata
        """
        cursor = self.conn.cursor()
        
        # Insert into FTS table
        cursor.execute("""
            INSERT OR REPLACE INTO documents_fts (doc_id, text, source, title, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc_id,
            text,
            metadata.get('source', ''),
            metadata.get('title', ''),
            str(metadata)
        ))
        
        # Insert into metadata table
        cursor.execute("""
            INSERT OR REPLACE INTO documents_meta (
                doc_id, source, url, owner, project, sprint, tags, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            metadata.get('source', ''),
            metadata.get('url', ''),
            metadata.get('owner', metadata.get('author', metadata.get('assignee', ''))),
            metadata.get('project', ''),
            metadata.get('sprint', ''),
            ','.join(metadata.get('tags', [])),
            metadata.get('last_seen', datetime.now().isoformat())
        ))
        
        self.conn.commit()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents using BM25
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters (project, sprint, etc.)
            
        Returns:
            List of results with scores
        """
        cursor = self.conn.cursor()
        
        # Build query
        sql = """
            SELECT 
                f.doc_id,
                f.text,
                f.source,
                f.title,
                m.url,
                m.owner,
                m.project,
                m.sprint,
                m.tags,
                bm25(documents_fts) as score
            FROM documents_fts f
            LEFT JOIN documents_meta m ON f.doc_id = m.doc_id
            WHERE documents_fts MATCH ?
        """
        
        params = [query]
        
        # Add filters
        if filters:
            if filters.get('project'):
                sql += " AND m.project = ?"
                params.append(filters['project'])
            
            if filters.get('sprint'):
                sql += " AND m.sprint = ?"
                params.append(filters['sprint'])
        
        sql += " ORDER BY score LIMIT ?"
        params.append(top_k)
        
        try:
            cursor.execute(sql, params)
            results = []
            
            for row in cursor.fetchall():
                results.append({
                    'doc_id': row[0],
                    'text': row[1],
                    'source': row[2],
                    'title': row[3],
                    'url': row[4],
                    'owner': row[5],
                    'project': row[6],
                    'sprint': row[7],
                    'tags': row[8].split(',') if row[8] else [],
                    'score': abs(row[9]),  # BM25 scores are negative
                    'retrieval_method': 'bm25'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.conn.close()


class VectorRetriever:
    """Vector search using Qdrant"""
    
    def __init__(self, url: str, collection_name: str = "documents"):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using vector similarity
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filters: Optional filters (project, sprint, since_days)
            
        Returns:
            List of results with scores
        """
        # Build Qdrant filter
        qdrant_filter = None
        if filters:
            conditions = []
            
            if filters.get('project'):
                conditions.append(
                    FieldCondition(
                        key="project",
                        match=MatchValue(value=filters['project'])
                    )
                )
            
            if filters.get('sprint'):
                conditions.append(
                    FieldCondition(
                        key="sprint",
                        match=MatchValue(value=filters['sprint'])
                    )
                )
            
            if filters.get('since_days'):
                cutoff_date = (datetime.now() - timedelta(days=filters['since_days'])).isoformat()
                conditions.append(
                    FieldCondition(
                        key="last_seen",
                        range=Range(gte=cutoff_date)
                    )
                )
            
            if conditions:
                qdrant_filter = Filter(must=conditions)
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True
            )
            
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    'doc_id': str(hit.id),
                    'text': hit.payload.get('text', ''),
                    'source': hit.payload.get('source', ''),
                    'title': hit.payload.get('title', ''),
                    'url': hit.payload.get('url', ''),
                    'owner': hit.payload.get('owner', hit.payload.get('author', hit.payload.get('assignee', ''))),
                    'project': hit.payload.get('project', ''),
                    'sprint': hit.payload.get('sprint', ''),
                    'tags': hit.payload.get('tags', []),
                    'score': hit.score,
                    'retrieval_method': 'vector'
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []


class HybridRetriever:
    """Hybrid retrieval combining BM25 and vector search with RRF fusion"""
    
    def __init__(
        self,
        qdrant_url: str,
        collection_name: str = "documents",
        bm25_db_path: str = "/app/data/bm25_index.db"
    ):
        self.vector_retriever = VectorRetriever(qdrant_url, collection_name)
        self.bm25_retriever = BM25Retriever(bm25_db_path)
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for query
        
        Args:
            query: Query text
            
        Returns:
            Query embedding vector
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('EMERGENT_LLM_KEY'))
            
            response = client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    def reciprocal_rank_fusion(
        self,
        results_list: List[List[Dict[str, Any]]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Fuse multiple result sets using Reciprocal Rank Fusion (RRF)
        
        RRF formula: score = sum(1 / (k + rank))
        
        Args:
            results_list: List of result sets from different retrievers
            k: RRF constant (default: 60)
            
        Returns:
            Fused and ranked results
        """
        doc_scores = {}
        doc_data = {}
        
        for results in results_list:
            for rank, doc in enumerate(results, start=1):
                doc_id = doc['doc_id']
                
                # RRF score
                score = 1.0 / (k + rank)
                
                if doc_id in doc_scores:
                    doc_scores[doc_id] += score
                else:
                    doc_scores[doc_id] = score
                    doc_data[doc_id] = doc
        
        # Sort by fused score
        fused_results = []
        for doc_id, score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            result = doc_data[doc_id].copy()
            result['fused_score'] = score
            fused_results.append(result)
        
        return fused_results
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        project: Optional[str] = None,
        sprint: Optional[str] = None,
        since_days: Optional[int] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 and vector retrieval
        
        Args:
            query: Search query
            top_k: Number of results to return
            project: Filter by project
            sprint: Filter by sprint
            since_days: Filter by last N days
            use_hybrid: If False, use vector search only
            
        Returns:
            Fused search results
        """
        filters = {}
        if project:
            filters['project'] = project
        if sprint:
            filters['sprint'] = sprint
        if since_days:
            filters['since_days'] = since_days
        
        # Get vector results
        logger.info(f"Generating embedding for query: {query}")
        query_vector = await self.generate_query_embedding(query)
        
        logger.info("Performing vector search...")
        vector_results = await self.vector_retriever.search(
            query_vector=query_vector,
            top_k=top_k * 2,  # Get more for fusion
            filters=filters
        )
        
        if not use_hybrid:
            return vector_results[:top_k]
        
        # Get BM25 results
        logger.info("Performing BM25 search...")
        bm25_results = self.bm25_retriever.search(
            query=query,
            top_k=top_k * 2,  # Get more for fusion
            filters=filters
        )
        
        # Fuse results
        logger.info("Fusing results with RRF...")
        fused_results = self.reciprocal_rank_fusion([vector_results, bm25_results])
        
        return fused_results[:top_k]
    
    def close(self):
        """Close connections"""
        self.bm25_retriever.close()


# Global retriever instance
_retriever = None


def get_retriever() -> HybridRetriever:
    """Get or create hybrid retriever singleton"""
    global _retriever
    if _retriever is None:
        qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
        _retriever = HybridRetriever(qdrant_url)
    return _retriever
