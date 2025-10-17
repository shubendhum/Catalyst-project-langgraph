"""
Learning Service
Learns from past projects to improve future performance
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from sklearn.metrics.pairwise import cosine_similarity
import logging
import json

logger = logging.getLogger(__name__)


class LearningService:
    """Learns from project history to improve suggestions"""
    
    def __init__(self, db=None):
        self.db = db
        
        # In-memory storage for patterns (would use vector DB in production)
        self.patterns = []
        self.pattern_embeddings = []
        
        # Simple embedding dimensions (would use proper embeddings in production)
        self.embedding_dim = 128
    
    def _create_simple_embedding(self, text: str) -> np.ndarray:
        """
        Create simple embedding from text
        In production, this would use a proper embedding model like Sentence Transformers
        """
        # Normalize text
        text = text.lower().strip()
        
        # Use simple character-based hashing for embedding
        # This is a placeholder - real implementation would use proper embeddings
        embedding = np.zeros(self.embedding_dim)
        
        for i, char in enumerate(text[:self.embedding_dim]):
            embedding[i % self.embedding_dim] += ord(char) / 1000.0
        
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
        
        if not self.patterns:
            # Load from database if available
            if self.db:
                await self._load_patterns_from_db()
        
        if not self.patterns:
            return []
        
        # Create embedding for query
        tech_stack = tech_stack or []
        query_text = f"{task_description} {' '.join(tech_stack)}"
        query_embedding = self._create_simple_embedding(query_text)
        
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
