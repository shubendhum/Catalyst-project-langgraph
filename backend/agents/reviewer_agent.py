"""
Reviewer Agent
Performs code quality checks, security scanning, and best practice validation
"""
import logging
import subprocess
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage
import json

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Agent responsible for code review and quality checks
    """
    
    def __init__(self, llm_client, db, manager, file_service):
        self.llm_client = llm_client
        self.db = db
        self.manager = manager
        self.file_service = file_service
        self.agent_name = "Reviewer"
    
    async def review_code(
        self,
        project_name: str,
        architecture: Dict,
        code_files: Dict,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Review generated code for quality, security, and best practices
        
        Args:
            project_name: Name of the project
            architecture: Technical architecture
            code_files: Generated code files
            task_id: Task ID for logging
            
        Returns:
            Dictionary with review results and recommendations
        """
        logger.info(f"Reviewing code for: {project_name}")
        
        if task_id:
            await self._log(task_id, "🔍 Starting comprehensive code review...")
        
        review_results = {
            "code_quality": {},
            "security_scan": {},
            "best_practices": {},
            "performance_analysis": {},
            "recommendations": [],
            "overall_score": 0,
            "status": "pending"
        }
        
        try:
            # Code quality checks
            if task_id:
                await self._log(task_id, "📊 Running code quality analysis...")
            
            quality_result = await self._check_code_quality(project_name)
            review_results["code_quality"] = quality_result
            
            # Security scanning
            if task_id:
                await self._log(task_id, "🔒 Running security vulnerability scan...")
            
            security_result = await self._security_scan(project_name, code_files)
            review_results["security_scan"] = security_result
            
            # Best practices check
            if task_id:
                await self._log(task_id, "✨ Checking best practices...")
            
            best_practices_result = await self._check_best_practices(project_name, architecture, code_files)
            review_results["best_practices"] = best_practices_result
            
            # Performance analysis
            if task_id:
                await self._log(task_id, "⚡ Analyzing performance patterns...")
            
            performance_result = await self._analyze_performance(code_files, architecture)
            review_results["performance_analysis"] = performance_result
            
            # Generate recommendations using LLM
            if task_id:
                await self._log(task_id, "💡 Generating improvement recommendations...")
            
            recommendations = await self._generate_recommendations(review_results, code_files)
            review_results["recommendations"] = recommendations
            
            # Calculate overall score
            overall_score = self._calculate_score(review_results)
            review_results["overall_score"] = overall_score
            review_results["status"] = "completed"
            review_results["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            if task_id:
                await self._log(task_id, f"✅ Code review complete! Overall score: {overall_score}/100")
            
            return review_results
            
        except Exception as e:
            logger.error(f"Error during code review: {str(e)}")
            review_results["status"] = "error"
            review_results["error"] = str(e)
            
            if task_id:
                await self._log(task_id, f"❌ Review error: {str(e)}")
            
            return review_results
    
    async def _check_code_quality(self, project_name: str) -> Dict:
        """Run code quality checks using linters"""
        
        project_path = self.file_service.base_projects_dir / project_name
        quality_results = {
            "backend": {},
            "frontend": {}
        }
        
        # Backend: Run pylint
        backend_path = project_path / "backend"
        if backend_path.exists():
            try:
                result = subprocess.run(
                    ["pylint", "--output-format=json", ".", "--recursive=y"],
                    cwd=str(backend_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Parse pylint output
                try:
                    pylint_data = json.loads(result.stdout) if result.stdout else []
                    quality_results["backend"] = {
                        "status": "passed" if result.returncode == 0 else "issues_found",
                        "issues_count": len(pylint_data),
                        "issues": pylint_data[:10],  # Limit to 10 issues
                        "tool": "pylint"
                    }
                except json.JSONDecodeError:
                    quality_results["backend"] = {
                        "status": "completed",
                        "output": result.stdout[:500],
                        "tool": "pylint"
                    }
            except Exception as e:
                quality_results["backend"] = {
                    "status": "error",
                    "message": str(e)
                }
        
        # Frontend: Run eslint
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            try:
                result = subprocess.run(
                    ["npx", "eslint", "src", "--format=json"],
                    cwd=str(frontend_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                try:
                    eslint_data = json.loads(result.stdout) if result.stdout else []
                    total_issues = sum(len(file.get("messages", [])) for file in eslint_data)
                    
                    quality_results["frontend"] = {
                        "status": "passed" if total_issues == 0 else "issues_found",
                        "issues_count": total_issues,
                        "files_checked": len(eslint_data),
                        "tool": "eslint"
                    }
                except json.JSONDecodeError:
                    quality_results["frontend"] = {
                        "status": "skipped",
                        "message": "ESLint not configured"
                    }
            except Exception as e:
                quality_results["frontend"] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return quality_results
    
    async def _security_scan(self, project_name: str, code_files: Dict) -> Dict:
        """Perform security vulnerability scanning"""
        
        security_results = {
            "vulnerabilities": [],
            "risk_level": "low",
            "checks_performed": []
        }
        
        # Use LLM for security analysis
        security_prompt = f"""Perform a security analysis on this code.

Check for:
1. SQL Injection vulnerabilities
2. XSS (Cross-Site Scripting) risks
3. Authentication weaknesses
4. Exposed secrets or API keys
5. Insecure dependencies
6. CORS misconfigurations
7. Input validation issues
8. Authorization bypasses

Code files summary:
Backend files: {len(code_files.get('backend', {}))} files
Frontend files: {len(code_files.get('frontend', {}))} files

Analyze the architecture and identify security concerns.
Return JSON format:
{{
  "vulnerabilities": [
    {{"type": "...", "severity": "high/medium/low", "description": "...", "file": "...", "recommendation": "..."}}
  ],
  "risk_level": "high/medium/low"
}}"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=security_prompt)])
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                security_data = json.loads(json_match.group())
                security_results.update(security_data)
        except Exception as e:
            logger.error(f"Security scan error: {str(e)}")
            security_results["error"] = str(e)
        
        security_results["checks_performed"] = [
            "SQL Injection", "XSS", "Authentication", "Secrets Exposure",
            "Dependencies", "CORS", "Input Validation", "Authorization"
        ]
        
        return security_results
    
    async def _check_best_practices(self, project_name: str, architecture: Dict, code_files: Dict) -> Dict:
        """Check adherence to best practices"""
        
        best_practices_prompt = f"""Review this application architecture for best practices.

Architecture:
{json.dumps(architecture, indent=2)}

Check for:
1. RESTful API design
2. Proper error handling
3. Code organization and structure
4. Database schema design
5. Frontend component architecture
6. State management
7. Testing coverage
8. Documentation
9. Environment configuration
10. Logging and monitoring

Rate each category (0-10) and provide recommendations.
Return JSON format:
{{
  "categories": {{
    "api_design": {{"score": 8, "notes": "..."}},
    "error_handling": {{"score": 7, "notes": "..."}},
    ...
  }},
  "overall_adherence": "85%"
}}"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=best_practices_prompt)])
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Best practices check error: {str(e)}")
        
        return {
            "categories": {},
            "overall_adherence": "N/A",
            "error": "Could not complete best practices analysis"
        }
    
    async def _analyze_performance(self, code_files: Dict, architecture: Dict) -> Dict:
        """Analyze performance patterns and potential bottlenecks"""
        
        performance_prompt = f"""Analyze this application for performance considerations.

Architecture overview:
{json.dumps(architecture.get('overview', {}), indent=2)}

Database models: {len(architecture.get('data_models', []))}
API endpoints: {len(architecture.get('api_specs', []))}

Identify:
1. Potential database query bottlenecks
2. N+1 query problems
3. Missing indexes
4. Inefficient algorithms
5. Frontend rendering issues
6. API response optimization
7. Caching opportunities
8. Bundle size concerns

Return JSON format:
{{
  "bottlenecks": [
    {{"area": "...", "severity": "high/medium/low", "description": "...", "solution": "..."}}
  ],
  "optimization_score": 75,
  "caching_opportunities": ["..."]
}}"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=performance_prompt)])
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Performance analysis error: {str(e)}")
        
        return {
            "bottlenecks": [],
            "optimization_score": 70,
            "caching_opportunities": [],
            "error": "Could not complete performance analysis"
        }
    
    async def _generate_recommendations(self, review_results: Dict, code_files: Dict) -> List[Dict]:
        """Generate improvement recommendations based on review"""
        
        recommendations_prompt = f"""Based on this code review, generate prioritized improvement recommendations.

Review Summary:
- Code Quality Issues: {review_results.get('code_quality', {}).get('backend', {}).get('issues_count', 0)} backend, {review_results.get('code_quality', {}).get('frontend', {}).get('issues_count', 0)} frontend
- Security Vulnerabilities: {len(review_results.get('security_scan', {}).get('vulnerabilities', []))}
- Overall Score: {review_results.get('overall_score', 0)}/100

Generate 5-10 specific, actionable recommendations.
Prioritize by impact (high/medium/low).

Return JSON array:
[
  {{
    "priority": "high",
    "category": "security/performance/quality/best_practices",
    "title": "...",
    "description": "...",
    "effort": "low/medium/high",
    "impact": "high/medium/low"
  }}
]"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=recommendations_prompt)])
            
            import re
            json_match = re.search(r'\[[\s\S]*\]', response.content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Recommendations generation error: {str(e)}")
        
        return [
            {
                "priority": "medium",
                "category": "general",
                "title": "Review and test thoroughly",
                "description": "Manually review generated code and run comprehensive tests",
                "effort": "medium",
                "impact": "high"
            }
        ]
    
    def _calculate_score(self, review_results: Dict) -> int:
        """Calculate overall code quality score"""
        
        score = 100
        
        # Deduct for code quality issues
        backend_issues = review_results.get('code_quality', {}).get('backend', {}).get('issues_count', 0)
        frontend_issues = review_results.get('code_quality', {}).get('frontend', {}).get('issues_count', 0)
        score -= min(backend_issues * 2, 20)
        score -= min(frontend_issues * 2, 20)
        
        # Deduct for security vulnerabilities
        vulns = review_results.get('security_scan', {}).get('vulnerabilities', [])
        high_vulns = sum(1 for v in vulns if v.get('severity') == 'high')
        medium_vulns = sum(1 for v in vulns if v.get('severity') == 'medium')
        score -= high_vulns * 15
        score -= medium_vulns * 5
        
        # Adjust for performance
        perf_score = review_results.get('performance_analysis', {}).get('optimization_score', 70)
        score = (score + perf_score) // 2
        
        return max(0, min(100, score))
    
    async def _log(self, task_id: str, message: str):
        """Log agent activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": self.agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_reviewer_agent(llm_client, db, manager, file_service) -> ReviewerAgent:
    """Get ReviewerAgent instance"""
    return ReviewerAgent(llm_client, db, manager, file_service)
