"""
RAG Ingest Pipeline CLI
Ingests documents from multiple sources into Qdrant vector database

Usage:
    python -m tools.ingest --confluence-space MYSPACE
    python -m tools.ingest --jira-jql "project=MYPROJ AND sprint=1"
    python -m tools.ingest --pdf /path/to/docs/
    python -m tools.ingest --servicedesk-url https://servicedesk.company.com
    python -m tools.ingest --since 30  # Last 30 days
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib
import json

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunks documents with overlap"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunks with metadata
        """
        # Simple word-based chunking (can be enhanced with tiktoken)
        words = text.split()
        chunks = []
        
        i = 0
        chunk_idx = 0
        while i < len(words):
            # Get chunk
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Create chunk with metadata
            chunk = {
                'text': chunk_text,
                'metadata': {
                    **metadata,
                    'chunk_index': chunk_idx,
                    'chunk_start': i,
                    'chunk_end': i + len(chunk_words)
                }
            }
            chunks.append(chunk)
            
            # Move forward with overlap
            i += self.chunk_size - self.overlap
            chunk_idx += 1
        
        logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks


class ConfluenceIngester:
    """Ingest documents from Confluence"""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url
        self.username = username
        self.api_token = api_token
    
    async def ingest_space(self, space_key: str, since_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ingest all pages from a Confluence space
        
        Args:
            space_key: Confluence space key
            since_days: Only ingest pages modified in last N days
            
        Returns:
            List of documents with metadata
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth
        except ImportError:
            logger.error("requests library not installed. Install with: pip install requests")
            return []
        
        logger.info(f"Ingesting Confluence space: {space_key}")
        
        documents = []
        start = 0
        limit = 50
        
        # Calculate since timestamp if specified
        since_timestamp = None
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)
            since_timestamp = since_date.isoformat()
        
        while True:
            # Query Confluence API
            url = f"{self.base_url}/rest/api/content"
            params = {
                'spaceKey': space_key,
                'expand': 'body.storage,version,metadata.labels',
                'start': start,
                'limit': limit,
                'type': 'page'
            }
            
            try:
                response = requests.get(
                    url,
                    params=params,
                    auth=HTTPBasicAuth(self.username, self.api_token),
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch Confluence pages: {e}")
                break
            
            results = data.get('results', [])
            if not results:
                break
            
            for page in results:
                # Check if page is recent enough
                last_modified = page.get('version', {}).get('when')
                if since_timestamp and last_modified and last_modified < since_timestamp:
                    continue
                
                # Extract content
                title = page.get('title', '')
                body = page.get('body', {}).get('storage', {}).get('value', '')
                
                # Remove HTML tags (simple approach)
                import re
                text = re.sub(r'<[^>]+>', '', body)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Extract labels
                labels = [label.get('name', '') for label in page.get('metadata', {}).get('labels', {}).get('results', [])]
                
                document = {
                    'text': f"{title}\n\n{text}",
                    'metadata': {
                        'source': 'confluence',
                        'source_type': 'confluence',
                        'space_key': space_key,
                        'page_id': page.get('id'),
                        'title': title,
                        'url': f"{self.base_url}{page.get('_links', {}).get('webui', '')}",
                        'author': page.get('version', {}).get('by', {}).get('displayName', 'Unknown'),
                        'last_modified': last_modified,
                        'tags': labels,
                        'last_seen': datetime.now().isoformat()
                    }
                }
                documents.append(document)
            
            # Check if there are more pages
            if len(results) < limit:
                break
            start += limit
        
        logger.info(f"Fetched {len(documents)} documents from Confluence space {space_key}")
        return documents


class JiraIngester:
    """Ingest issues from Jira"""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url
        self.username = username
        self.api_token = api_token
    
    async def ingest_jql(self, jql: str, since_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ingest Jira issues using JQL query
        
        Args:
            jql: JQL query string
            since_days: Only ingest issues updated in last N days
            
        Returns:
            List of documents with metadata
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth
        except ImportError:
            logger.error("requests library not installed. Install with: pip install requests")
            return []
        
        logger.info(f"Ingesting Jira issues with JQL: {jql}")
        
        # Add time filter if specified
        if since_days:
            jql = f"({jql}) AND updated >= -{since_days}d"
        
        documents = []
        start_at = 0
        max_results = 50
        
        while True:
            # Query Jira API
            url = f"{self.base_url}/rest/api/2/search"
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,assignee,reporter,created,updated,labels,project,issuetype,components,fixVersions,customfield_*'
            }
            
            try:
                response = requests.get(
                    url,
                    params=params,
                    auth=HTTPBasicAuth(self.username, self.api_token),
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch Jira issues: {e}")
                break
            
            issues = data.get('issues', [])
            if not issues:
                break
            
            for issue in issues:
                fields = issue.get('fields', {})
                
                # Build text content
                summary = fields.get('summary', '')
                description = fields.get('description', '') or ''
                
                # Extract sprint info if available (customfield varies by Jira instance)
                sprint = None
                for key, value in fields.items():
                    if 'sprint' in key.lower() and value:
                        if isinstance(value, list) and len(value) > 0:
                            sprint = str(value[0])
                        else:
                            sprint = str(value)
                        break
                
                text = f"{summary}\n\n{description}"
                
                document = {
                    'text': text,
                    'metadata': {
                        'source': 'jira',
                        'source_type': 'jira',
                        'issue_key': issue.get('key'),
                        'title': summary,
                        'url': f"{self.base_url}/browse/{issue.get('key')}",
                        'status': fields.get('status', {}).get('name'),
                        'priority': fields.get('priority', {}).get('name'),
                        'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else 'Unassigned',
                        'reporter': fields.get('reporter', {}).get('displayName', 'Unknown'),
                        'project': fields.get('project', {}).get('key'),
                        'sprint': sprint,
                        'issue_type': fields.get('issuetype', {}).get('name'),
                        'created': fields.get('created'),
                        'updated': fields.get('updated'),
                        'tags': fields.get('labels', []),
                        'last_seen': datetime.now().isoformat()
                    }
                }
                documents.append(document)
            
            # Check if there are more issues
            if start_at + max_results >= data.get('total', 0):
                break
            start_at += max_results
        
        logger.info(f"Fetched {len(documents)} issues from Jira")
        return documents


class PDFIngester:
    """Ingest PDF documents"""
    
    async def ingest_pdfs(self, path: str) -> List[Dict[str, Any]]:
        """
        Ingest PDF files from a directory or single file
        
        Args:
            path: Path to PDF file or directory
            
        Returns:
            List of documents with metadata
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.error("pypdf library not installed. Install with: pip install pypdf")
            return []
        
        logger.info(f"Ingesting PDFs from: {path}")
        
        pdf_path = Path(path)
        documents = []
        
        # Get list of PDF files
        if pdf_path.is_file():
            pdf_files = [pdf_path]
        elif pdf_path.is_dir():
            pdf_files = list(pdf_path.rglob('*.pdf'))
        else:
            logger.error(f"Path not found: {path}")
            return []
        
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(str(pdf_file))
                text_parts = []
                
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    text_parts.append(text)
                
                full_text = '\n\n'.join(text_parts)
                
                # Get file metadata
                metadata_obj = reader.metadata if hasattr(reader, 'metadata') else {}
                
                document = {
                    'text': full_text,
                    'metadata': {
                        'source': 'pdf',
                        'source_type': 'pdf',
                        'filename': pdf_file.name,
                        'filepath': str(pdf_file.absolute()),
                        'title': metadata_obj.get('/Title', pdf_file.stem) if metadata_obj else pdf_file.stem,
                        'author': metadata_obj.get('/Author', 'Unknown') if metadata_obj else 'Unknown',
                        'page_count': len(reader.pages),
                        'created': metadata_obj.get('/CreationDate') if metadata_obj else None,
                        'last_seen': datetime.now().isoformat()
                    }
                }
                documents.append(document)
                
                logger.info(f"Ingested PDF: {pdf_file.name} ({len(reader.pages)} pages)")
                
            except Exception as e:
                logger.error(f"Failed to ingest PDF {pdf_file}: {e}")
        
        logger.info(f"Ingested {len(documents)} PDF documents")
        return documents


class ServiceDeskIngester:
    """Ingest ServiceDesk tickets"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    async def ingest_tickets(self, since_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ingest ServiceDesk tickets
        
        Args:
            since_days: Only ingest tickets updated in last N days
            
        Returns:
            List of documents with metadata
        """
        # Placeholder - implement based on your ServiceDesk API
        logger.warning("ServiceDesk ingestion not yet implemented")
        return []


class VectorStore:
    """Qdrant vector store operations"""
    
    def __init__(self, url: str, collection_name: str = "documents"):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.embedding_dim = 1536  # OpenAI ada-002 dimension
    
    def ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}'")
    
    async def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Upsert chunks into Qdrant with embeddings
        
        Args:
            chunks: List of chunks with text and metadata
        """
        if not chunks:
            return
        
        # Generate embeddings (placeholder - use actual embeddings)
        # In production, use OpenAI API or local model
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        
        try:
            # Try to use OpenAI embeddings
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('EMERGENT_LLM_KEY'))
            
            # Batch embed
            texts = [chunk['text'][:8000] for chunk in chunks]  # Truncate to max length
            
            embeddings = []
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embeddings.create(
                    input=batch,
                    model="text-embedding-ada-002"
                )
                embeddings.extend([item.embedding for item in response.data])
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")
            logger.warning("Using random embeddings (for testing only)")
            import numpy as np
            embeddings = [np.random.rand(self.embedding_dim).tolist() for _ in chunks]
        
        # Create points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate unique ID from content hash
            content_hash = hashlib.md5(chunk['text'].encode()).hexdigest()
            point_id = int(content_hash[:8], 16)  # Convert first 8 chars of hash to int
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    'text': chunk['text'],
                    **chunk['metadata']
                }
            )
            points.append(point)
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Upserted {len(points)} chunks to Qdrant")


async def main():
    """Main ingestion pipeline"""
    parser = argparse.ArgumentParser(description='RAG Ingest Pipeline')
    parser.add_argument('--confluence-space', help='Confluence space key')
    parser.add_argument('--jira-jql', help='Jira JQL query')
    parser.add_argument('--pdf', help='Path to PDF file or directory')
    parser.add_argument('--servicedesk-url', help='ServiceDesk URL')
    parser.add_argument('--since', type=int, help='Only ingest items from last N days')
    parser.add_argument('--chunk-size', type=int, default=512, help='Chunk size in tokens')
    parser.add_argument('--overlap', type=int, default=64, help='Chunk overlap in tokens')
    parser.add_argument('--collection', default='documents', help='Qdrant collection name')
    
    args = parser.parse_args()
    
    # Get configuration from environment
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    confluence_url = os.getenv('CONFLUENCE_URL')
    confluence_username = os.getenv('CONFLUENCE_USERNAME')
    confluence_token = os.getenv('CONFLUENCE_API_TOKEN')
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_token = os.getenv('JIRA_API_TOKEN')
    servicedesk_url = args.servicedesk_url or os.getenv('SERVICEDESK_URL')
    servicedesk_key = os.getenv('SERVICEDESK_API_KEY')
    
    # Initialize components
    chunker = DocumentChunker(chunk_size=args.chunk_size, overlap=args.overlap)
    vector_store = VectorStore(url=qdrant_url, collection_name=args.collection)
    
    # Ensure collection exists
    vector_store.ensure_collection()
    
    documents = []
    
    # Ingest from Confluence
    if args.confluence_space:
        if not all([confluence_url, confluence_username, confluence_token]):
            logger.error("Confluence credentials not configured. Set CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN")
        else:
            ingester = ConfluenceIngester(confluence_url, confluence_username, confluence_token)
            docs = await ingester.ingest_space(args.confluence_space, args.since)
            documents.extend(docs)
    
    # Ingest from Jira
    if args.jira_jql:
        if not all([jira_url, jira_username, jira_token]):
            logger.error("Jira credentials not configured. Set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        else:
            ingester = JiraIngester(jira_url, jira_username, jira_token)
            docs = await ingester.ingest_jql(args.jira_jql, args.since)
            documents.extend(docs)
    
    # Ingest PDFs
    if args.pdf:
        ingester = PDFIngester()
        docs = await ingester.ingest_pdfs(args.pdf)
        documents.extend(docs)
    
    # Ingest ServiceDesk
    if servicedesk_url:
        if not servicedesk_key:
            logger.error("ServiceDesk API key not configured. Set SERVICEDESK_API_KEY")
        else:
            ingester = ServiceDeskIngester(servicedesk_url, servicedesk_key)
            docs = await ingester.ingest_tickets(args.since)
            documents.extend(docs)
    
    if not documents:
        logger.warning("No documents to ingest. Specify at least one source.")
        return
    
    logger.info(f"Total documents fetched: {len(documents)}")
    
    # Chunk all documents
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_text(doc['text'], doc['metadata'])
        all_chunks.extend(chunks)
    
    logger.info(f"Total chunks created: {len(all_chunks)}")
    
    # Upsert to vector store
    await vector_store.upsert_chunks(all_chunks)
    
    logger.info("✅ Ingestion complete!")


if __name__ == '__main__':
    asyncio.run(main())
