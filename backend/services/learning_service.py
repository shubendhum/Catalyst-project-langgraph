"""
Learning Service
Learns from past projects to improve future performance
Uses Qdrant vector DB when available, falls back to in-memory storage
Uses OpenAI embeddings for high-quality semantic understanding
"""

import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from sklearn.metrics.pairwise import cosine_similarity
import logging
import json

# Disable SSL verification for corporate environments
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Set environment variables to disable SSL verification
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_CERT_FILE'] = ''

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Try to import Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant not available, using in-memory vector storage")

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, embeddings disabled")



class LearningService:
    """Learns from project history to improve suggestions"""
    
    def __init__(self, db=None):
        self.db = db
        
        # Try to connect to Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_client = None
        self.collection_name = "catalyst_learning"
        
        # OpenAI embeddings configuration
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension
        self.openai_client = None
        
        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(url=qdrant_url, timeout=5.0)
                # Create collection if it doesn't exist
                collections = self.qdrant_client.get_collections().collections
                if not any(c.name == self.collection_name for c in collections):
                    self.qdrant_client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
                    )
                logger.info(f"✅ Connected to Qdrant at {qdrant_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant: {e}. Using in-memory storage.")
                self.qdrant_client = None
        
        # Initialize OpenAI client for embeddings
        if OPENAI_AVAILABLE:
            try:
                # Get API key from environment (Emergent LLM Key or OpenAI key)
                api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info("✅ OpenAI embeddings initialized (using Emergent LLM Key)")
                else:
                    logger.warning("No API key found for OpenAI embeddings")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # In-memory storage as fallback
        self.patterns = []
        self.pattern_embeddings = []
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """
        Create embedding from text using OpenAI API
        Falls back to simple hashing if OpenAI not available
        """
        # Use OpenAI embeddings if available
        if self.openai_client:
        if self.embedding_model:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                embedding = np.array(response.data[0].embedding)
                return embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}. Using fallback.")
        
        # Fallback to simple embedding
        # Normalize text
        text = text.lower().strip()
        
        # Use simple character-based hashing for embedding
        embedding = np.zeros(self.embedding_dim)
        
        # Simple hash-based embedding (fallback)
        for i, char in enumerate(text[:min(len(text), 100)]):
            idx = (ord(char) * (i + 1)) % self.embedding_dim
            embedding[idx] += 1.0 / (i + 1)
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    async def learn_from_project(
        self,
        project_id: str,
        task_description: str,
        tech_stack: List[str],
        success: bool,
        metrics: Dict
    ) -> Dict:
        """Extract learnings from completed project"""
        
        learning_entry = {
            "id": f"learning_{datetime.now().timestamp()}",
            "project_id": project_id,
            "task_description": task_description,
            "tech_stack": tech_stack,
            "success": success,
            "metrics": metrics,
            "patterns": self._extract_patterns(task_description, tech_stack),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create embedding
        embedding_text = f"{task_description} {' '.join(tech_stack)}"
        embedding = self._create_simple_embedding(embedding_text)
        
        # Store in Qdrant if available
        if self.qdrant_client:
            try:
                point_id = hash(learning_entry["id"]) % (2**31)  # Generate int ID
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=embedding.tolist(),
                            payload={
                                "project_id": project_id,
                                "task_description": task_description,
                                "tech_stack": tech_stack,
                                "success": success,
                                "metrics": metrics,
                                "patterns": learning_entry["patterns"],
                                "created_at": learning_entry["created_at"]
                            }
                        )
                    ]
                )
                logger.info(f"✅ Stored in Qdrant vector DB")
            except Exception as e:
                logger.error(f"Error storing in Qdrant: {e}")
        
        # Store in memory
        self.patterns.append(learning_entry)
        self.pattern_embeddings.append(embedding)
        
        # Store in database if available
        if self.db:
            try:
                learning_entry["embedding"] = embedding.tolist()
                await self.db.learning_entries.insert_one(learning_entry)
                logger.info(f"Stored learning entry for project {project_id}")
            except Exception as e:
                logger.error(f"Error storing learning entry: {e}")
        
        return {
            "learned": True,
            "patterns_extracted": len(learning_entry["patterns"]),
            "entry_id": learning_entry["id"]
        }
    
    def _extract_patterns(self, description: str, tech_stack: List[str]) -> List[str]:
        """Extract patterns from description and tech stack"""
        patterns = []
        
        description_lower = description.lower()
        
        # Common patterns
        pattern_keywords = {
            "authentication": ["auth", "login", "signup", "jwt", "session"],
            "crud_api": ["crud", "rest api", "endpoints", "database"],
            "real_time": ["websocket", "real-time", "realtime", "live updates"],
            "file_upload": ["upload", "file", "image", "media"],
            "payment": ["payment", "stripe", "billing", "subscription"],
            "email": ["email", "notification", "sendgrid", "smtp"],
            "search": ["search", "query", "filter", "elasticsearch"],
            "analytics": ["analytics", "tracking", "metrics", "dashboard"]
        }
        
        for pattern_name, keywords in pattern_keywords.items():
            if any(kw in description_lower for kw in keywords):
                patterns.append(pattern_name)
        
        # Add tech stack as patterns
        for tech in tech_stack:
            patterns.append(f"tech_{tech.lower()}")
        
        return list(set(patterns))  # Remove duplicates
    
    async def find_similar_projects(
        self,
        task_description: str,
        tech_stack: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar past projects"""
        
        tech_stack = tech_stack or []
        query_text = f"{task_description} {' '.join(tech_stack)}"
        query_embedding = self._create_simple_embedding(query_text)
        
        # Try Qdrant first
        if self.qdrant_client:
            try:
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=limit
                )
                
                results = []
                for hit in search_results:
                    result = {
                        **hit.payload,
                        "similarity": float(hit.score)
                    }
                    results.append(result)
                
                logger.info(f"✅ Found {len(results)} similar projects from Qdrant")
                return results
            except Exception as e:
                logger.error(f"Error searching Qdrant: {e}")
        
        # Fall back to in-memory search
        if not self.patterns:
            # Load from database if available
            if self.db:
                await self._load_patterns_from_db()
        
        if not self.patterns:
            return []
        
        # Calculate similarities
        similarities = []
        for i, pattern_embedding in enumerate(self.pattern_embeddings):
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                pattern_embedding.reshape(1, -1)
            )[0][0]
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches
        results = []
        for idx, similarity in similarities[:limit]:
            pattern = self.patterns[idx].copy()
            pattern["similarity"] = float(similarity)
            results.append(pattern)
        
        return results
    
    async def _load_patterns_from_db(self):
        """Load patterns from database"""
        if not self.db:
            return
        
        try:
            entries = await self.db.learning_entries.find().sort("created_at", -1).limit(100).to_list(100)
            
            for entry in entries:
                embedding = entry.get("embedding")
                if embedding:
                    self.patterns.append(entry)
                    self.pattern_embeddings.append(np.array(embedding))
            
            logger.info(f"Loaded {len(self.patterns)} learning patterns from database")
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
    
    async def suggest_improvements(
        self,
        project_id: str,
        current_metrics: Dict
    ) -> List[Dict]:
        """Suggest improvements based on historical data"""
        
        if not self.db:
            return []
        
        try:
            # Get project info
            project = await self.db.projects.find_one({"id": project_id})
            if not project:
                return []
            
            # Find similar successful projects
            similar = await self.find_similar_projects(
                project.get("description", ""),
                project.get("tech_stack", [])
            )
            
            successful_similar = [p for p in similar if p.get("success")]
            
            if not successful_similar:
                return []
            
            suggestions = []
            
            # Compare metrics with successful projects
            avg_metrics = self._calculate_average_metrics(successful_similar)
            
            # Suggest improvements based on metrics
            if current_metrics.get("completion_time_seconds", 0) > avg_metrics.get("completion_time_seconds", 0) * 1.2:
                suggestions.append({
                    "type": "performance",
                    "priority": "high",
                    "suggestion": "Task completion time is 20% slower than similar projects",
                    "recommendation": "Consider optimizing agent prompts or using faster models for simple tasks",
                    "potential_improvement": "20% faster completion"
                })
            
            if current_metrics.get("cost_usd", 0) > avg_metrics.get("cost_usd", 0) * 1.3:
                suggestions.append({
                    "type": "cost",
                    "priority": "high",
                    "suggestion": "Project costs are 30% higher than similar projects",
                    "recommendation": "Enable caching and use cheaper models for simpler tasks",
                    "potential_savings": f"${(current_metrics.get('cost_usd', 0) - avg_metrics.get('cost_usd', 0)):.2f}"
                })
            
            if current_metrics.get("code_quality_score", 100) < avg_metrics.get("code_quality_score", 85):
                suggestions.append({
                    "type": "quality",
                    "priority": "medium",
                    "suggestion": "Code quality below average for similar projects",
                    "recommendation": "Enable code review agent and increase test coverage",
                    "target_score": avg_metrics.get("code_quality_score", 85)
                })
            
            # Look for common patterns in successful projects
            common_patterns = self._find_common_patterns(successful_similar)
            
            for pattern in common_patterns:
                if pattern not in project.get("patterns_used", []):
                    suggestions.append({
                        "type": "pattern",
                        "priority": "medium",
                        "suggestion": f"Successful similar projects commonly use '{pattern}'",
                        "recommendation": f"Consider implementing {pattern} pattern",
                        "adoption_rate": f"{self._calculate_pattern_adoption(successful_similar, pattern):.0%}"
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    def _calculate_average_metrics(self, projects: List[Dict]) -> Dict:
        """Calculate average metrics from projects"""
        if not projects:
            return {}
        
        metrics = {}
        metric_keys = ["completion_time_seconds", "cost_usd", "code_quality_score", "iterations_needed"]
        
        for key in metric_keys:
            values = [
                p.get("metrics", {}).get(key, 0) 
                for p in projects 
                if p.get("metrics", {}).get(key) is not None
            ]
            if values:
                metrics[key] = sum(values) / len(values)
        
        return metrics
    
    def _find_common_patterns(self, projects: List[Dict]) -> List[str]:
        """Find patterns that appear in most successful projects"""
        pattern_counts = {}
        
        for project in projects:
            for pattern in project.get("patterns", []):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Return patterns that appear in at least 50% of projects
        threshold = len(projects) * 0.5
        return [
            pattern for pattern, count in pattern_counts.items()
            if count >= threshold
        ]
    
    def _calculate_pattern_adoption(self, projects: List[Dict], pattern: str) -> float:
        """Calculate what percentage of projects use a pattern"""
        if not projects:
            return 0.0
        
        count = sum(1 for p in projects if pattern in p.get("patterns", []))
        return count / len(projects)
    
    async def predict_success_probability(
        self,
        task_description: str,
        tech_stack: List[str]
    ) -> Dict:
        """Predict probability of successful completion"""
        
        similar = await self.find_similar_projects(task_description, tech_stack, limit=20)
        
        if not similar:
            return {
                "probability": 0.75,  # Default estimate
                "confidence": "low",
                "message": "No similar projects found for comparison"
            }
        
        # Calculate success rate
        successful = sum(1 for p in similar if p.get("success"))
        success_rate = successful / len(similar)
        
        # Adjust based on similarity scores
        weighted_success = sum(
            p.get("similarity", 0) for p in similar if p.get("success")
        )
        total_weight = sum(p.get("similarity", 0) for p in similar)
        
        if total_weight > 0:
            weighted_success_rate = weighted_success / total_weight
        else:
            weighted_success_rate = success_rate
        
        # Determine confidence
        confidence = "high" if len(similar) >= 10 else "medium" if len(similar) >= 5 else "low"
        
        return {
            "probability": weighted_success_rate,
            "confidence": confidence,
            "similar_projects": len(similar),
            "successful_similar": successful,
            "message": f"Based on {len(similar)} similar projects, {successful} were successful"
        }
    
    async def get_learning_stats(self) -> Dict:
        """Get learning system statistics"""
        stats = {
            "patterns_in_memory": len(self.patterns),
            "patterns_in_db": 0,
            "total_projects_learned": len(set(p.get("project_id") for p in self.patterns)),
            "successful_projects": sum(1 for p in self.patterns if p.get("success")),
        }
        
        if self.db:
            try:
                stats["patterns_in_db"] = await self.db.learning_entries.count_documents({})
            except:
                pass
        
        stats["success_rate"] = (
            stats["successful_projects"] / stats["patterns_in_memory"] 
            if stats["patterns_in_memory"] > 0 else 0
        )
        
        return stats


def get_learning_service(db=None) -> LearningService:
    """Factory function to get learning service"""
    return LearningService(db)
