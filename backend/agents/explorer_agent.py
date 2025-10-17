"""
Explorer Agent
Analyzes GitHub repositories, deployed applications, web apps, databases, and big data platforms
"""
import logging
import subprocess
import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage
from pathlib import Path
import tempfile
import shutil

logger = logging.getLogger(__name__)


class ExplorerAgent:
    """
    Agent responsible for exploring and analyzing existing systems
    """
    
    def __init__(self, llm_client, db, manager, file_service):
        self.llm_client = llm_client
        self.db = db
        self.manager = manager
        self.file_service = file_service
        self.agent_name = "Explorer"
    
    async def explore(
        self,
        target: str,
        target_type: str,  # "github", "url", "deployment", "database"
        credentials: Optional[Dict] = None,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Explore and analyze a target system
        
        Args:
            target: URL, GitHub repo, or connection string
            target_type: Type of target to explore
            credentials: Optional credentials for access
            task_id: Task ID for logging
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Exploring {target_type}: {target}")
        
        if task_id:
            await self._log(task_id, f"🔍 Starting exploration of {target_type}...")
        
        exploration_result = {
            "target": target,
            "target_type": target_type,
            "analysis": {},
            "recommendations": [],
            "status": "pending"
        }
        
        try:
            if target_type == "github":
                result = await self._explore_github_repo(target, credentials, task_id)
            elif target_type == "url":
                result = await self._explore_web_app(target, task_id)
            elif target_type == "deployment":
                result = await self._explore_deployment(target, task_id)
            elif target_type == "database":
                result = await self._explore_database(target, credentials, task_id)
            elif target_type == "bigdata":
                result = await self._explore_bigdata_platform(target, credentials, task_id)
            else:
                raise ValueError(f"Unknown target type: {target_type}")
            
            exploration_result["analysis"] = result
            exploration_result["status"] = "success"
            exploration_result["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Generate enhancement recommendations
            if task_id:
                await self._log(task_id, "💡 Generating enhancement recommendations...")
            
            recommendations = await self._generate_recommendations(result, target_type)
            exploration_result["recommendations"] = recommendations
            
            if task_id:
                await self._log(task_id, f"✅ Exploration complete! Found {len(recommendations)} recommendations")
            
            return exploration_result
            
        except Exception as e:
            logger.error(f"Error during exploration: {str(e)}")
            exploration_result["status"] = "error"
            exploration_result["error"] = str(e)
            
            if task_id:
                await self._log(task_id, f"❌ Exploration error: {str(e)}")
            
            return exploration_result
    
    async def _explore_github_repo(
        self,
        repo_url: str,
        credentials: Optional[Dict],
        task_id: Optional[str]
    ) -> Dict:
        """Explore and analyze GitHub repository"""
        
        if task_id:
            await self._log(task_id, "📦 Cloning repository...")
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp(prefix="catalyst_explore_")
        
        try:
            # Clone repository
            github_token = credentials.get("github_token") if credentials else None
            clone_url = self._prepare_clone_url(repo_url, github_token)
            
            result = subprocess.run(
                ["git", "clone", "--depth=1", clone_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to clone repository: {result.stderr}")
            
            if task_id:
                await self._log(task_id, "🔍 Analyzing repository structure...")
            
            # Analyze repository
            analysis = {
                "repo_url": repo_url,
                "file_structure": self._analyze_file_structure(temp_dir),
                "tech_stack": await self._detect_tech_stack(temp_dir),
                "dependencies": self._analyze_dependencies(temp_dir),
                "code_metrics": await self._analyze_code_metrics(temp_dir),
                "architecture": await self._detect_architecture(temp_dir),
                "documentation": self._analyze_documentation(temp_dir),
                "security": await self._analyze_security(temp_dir),
                "quality_score": 0
            }
            
            # Calculate quality score
            analysis["quality_score"] = self._calculate_quality_score(analysis)
            
            return analysis
            
        finally:
            # Cleanup temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _explore_web_app(self, url: str, task_id: Optional[str]) -> Dict:
        """Explore and analyze web application"""
        
        if task_id:
            await self._log(task_id, "🌐 Analyzing web application...")
        
        analysis = {
            "url": url,
            "status": "unknown",
            "frontend_tech": {},
            "api_endpoints": [],
            "performance": {},
            "security_headers": {},
            "accessibility": {}
        }
        
        try:
            # Fetch the web page
            if task_id:
                await self._log(task_id, "📡 Fetching application...")
            
            response = requests.get(url, timeout=30, headers={"User-Agent": "Catalyst-Explorer/1.0"})
            analysis["status"] = response.status_code
            
            # Analyze frontend technologies
            if task_id:
                await self._log(task_id, "🔍 Detecting frontend technologies...")
            
            analysis["frontend_tech"] = self._detect_frontend_tech(response.text, response.headers)
            
            # Check security headers
            analysis["security_headers"] = self._analyze_security_headers(response.headers)
            
            # Analyze performance
            analysis["performance"] = {
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_size_kb": len(response.content) / 1024
            }
            
            # Use LLM to analyze page structure
            if task_id:
                await self._log(task_id, "🤖 AI-analyzing application structure...")
            
            llm_analysis = await self._llm_analyze_webapp(url, response.text[:5000])  # Limit text
            analysis["llm_insights"] = llm_analysis
            
            return analysis
            
        except Exception as e:
            analysis["error"] = str(e)
            return analysis
    
    async def _explore_deployment(self, deployment_url: str, task_id: Optional[str]) -> Dict:
        """Explore deployed application"""
        
        if task_id:
            await self._log(task_id, "🚀 Analyzing deployment...")
        
        analysis = {
            "url": deployment_url,
            "health_check": {},
            "api_discovery": [],
            "environment": {},
            "monitoring": {}
        }
        
        try:
            # Health check
            health_endpoints = ["/health", "/api/health", "/healthz", "/_health"]
            for endpoint in health_endpoints:
                try:
                    resp = requests.get(f"{deployment_url}{endpoint}", timeout=10)
                    if resp.status_code == 200:
                        analysis["health_check"] = {
                            "endpoint": endpoint,
                            "status": "healthy",
                            "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
                        }
                        break
                except:
                    continue
            
            # API discovery
            if task_id:
                await self._log(task_id, "🔎 Discovering API endpoints...")
            
            common_api_paths = [
                "/api/docs", "/docs", "/swagger", "/api/swagger",
                "/api/v1", "/api/v2", "/graphql", "/api/graphql"
            ]
            
            for path in common_api_paths:
                try:
                    resp = requests.get(f"{deployment_url}{path}", timeout=10)
                    if resp.status_code == 200:
                        analysis["api_discovery"].append({
                            "path": path,
                            "status": resp.status_code,
                            "type": self._detect_api_type(resp)
                        })
                except:
                    continue
            
            # Detect environment and platform
            analysis["environment"] = await self._detect_deployment_platform(deployment_url)
            
            return analysis
            
        except Exception as e:
            analysis["error"] = str(e)
            return analysis
    
    async def _explore_database(
        self,
        connection_string: str,
        credentials: Optional[Dict],
        task_id: Optional[str]
    ) -> Dict:
        """Explore database schema and structure"""
        
        if task_id:
            await self._log(task_id, "🗄️  Analyzing database...")
        
        analysis = {
            "connection_string": self._sanitize_connection_string(connection_string),
            "database_type": self._detect_db_type(connection_string),
            "schema": {},
            "statistics": {},
            "optimization_suggestions": []
        }
        
        db_type = analysis["database_type"]
        
        try:
            if db_type == "mongodb":
                analysis = await self._explore_mongodb(connection_string, credentials, task_id)
            elif db_type == "postgresql":
                analysis = await self._explore_postgresql(connection_string, credentials, task_id)
            elif db_type == "mysql":
                analysis = await self._explore_mysql(connection_string, credentials, task_id)
            else:
                analysis["message"] = f"Database type {db_type} analysis not yet implemented"
            
            return analysis
            
        except Exception as e:
            analysis["error"] = str(e)
            return analysis
    
    async def _explore_bigdata_platform(
        self,
        platform_url: str,
        credentials: Optional[Dict],
        task_id: Optional[str]
    ) -> Dict:
        """Explore big data platforms (Hadoop, Spark, Kafka, etc.)"""
        
        if task_id:
            await self._log(task_id, "📊 Analyzing big data platform...")
        
        analysis = {
            "platform_url": platform_url,
            "platform_type": "unknown",
            "cluster_info": {},
            "data_sources": [],
            "processing_jobs": [],
            "metrics": {}
        }
        
        # Detect platform type
        platform_type = await self._detect_bigdata_platform(platform_url, credentials)
        analysis["platform_type"] = platform_type
        
        try:
            if platform_type == "kafka":
                analysis.update(await self._explore_kafka(platform_url, credentials, task_id))
            elif platform_type == "hadoop":
                analysis.update(await self._explore_hadoop(platform_url, credentials, task_id))
            elif platform_type == "spark":
                analysis.update(await self._explore_spark(platform_url, credentials, task_id))
            elif platform_type == "elasticsearch":
                analysis.update(await self._explore_elasticsearch(platform_url, credentials, task_id))
            else:
                # Generic big data platform analysis
                analysis = await self._generic_bigdata_analysis(platform_url, credentials, task_id)
            
            return analysis
            
        except Exception as e:
            analysis["error"] = str(e)
            return analysis
    
    def _prepare_clone_url(self, repo_url: str, token: Optional[str]) -> str:
        """Prepare GitHub clone URL with authentication"""
        if token and "github.com" in repo_url:
            # Add token to URL
            if repo_url.startswith("https://github.com/"):
                repo_url = repo_url.replace("https://github.com/", f"https://{token}@github.com/")
        return repo_url
    
    def _analyze_file_structure(self, repo_path: str) -> Dict:
        """Analyze repository file structure"""
        structure = {
            "total_files": 0,
            "total_directories": 0,
            "file_types": {},
            "main_directories": []
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
            
            structure["total_directories"] += len(dirs)
            structure["total_files"] += len(files)
            
            for file in files:
                ext = Path(file).suffix or "no_extension"
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
        
        # Get main directories
        try:
            structure["main_directories"] = [d for d in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, d)) and not d.startswith('.')]
        except:
            pass
        
        return structure
    
    async def _detect_tech_stack(self, repo_path: str) -> Dict:
        """Detect technology stack from repository"""
        tech_stack = {
            "frontend": [],
            "backend": [],
            "database": [],
            "devops": [],
            "languages": []
        }
        
        # Check for common files
        if os.path.exists(os.path.join(repo_path, "package.json")):
            tech_stack["frontend"].append("Node.js/JavaScript")
            try:
                with open(os.path.join(repo_path, "package.json")) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps:
                        tech_stack["frontend"].append("React")
                    if "vue" in deps:
                        tech_stack["frontend"].append("Vue.js")
                    if "angular" in deps:
                        tech_stack["frontend"].append("Angular")
                    if "next" in deps:
                        tech_stack["frontend"].append("Next.js")
            except:
                pass
        
        if os.path.exists(os.path.join(repo_path, "requirements.txt")) or os.path.exists(os.path.join(repo_path, "Pipfile")):
            tech_stack["backend"].append("Python")
            tech_stack["languages"].append("Python")
        
        if os.path.exists(os.path.join(repo_path, "go.mod")):
            tech_stack["backend"].append("Go")
            tech_stack["languages"].append("Go")
        
        if os.path.exists(os.path.join(repo_path, "pom.xml")) or os.path.exists(os.path.join(repo_path, "build.gradle")):
            tech_stack["backend"].append("Java")
            tech_stack["languages"].append("Java")
        
        if os.path.exists(os.path.join(repo_path, "Dockerfile")):
            tech_stack["devops"].append("Docker")
        
        if os.path.exists(os.path.join(repo_path, "docker-compose.yml")):
            tech_stack["devops"].append("Docker Compose")
        
        if os.path.exists(os.path.join(repo_path, ".github/workflows")):
            tech_stack["devops"].append("GitHub Actions")
        
        return tech_stack
    
    def _analyze_dependencies(self, repo_path: str) -> Dict:
        """Analyze project dependencies"""
        dependencies = {
            "frontend": [],
            "backend": [],
            "total_count": 0
        }
        
        # Frontend dependencies
        package_json = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    deps = list(pkg.get("dependencies", {}).keys())
                    dependencies["frontend"] = deps[:20]  # Limit to 20
                    dependencies["total_count"] += len(deps)
            except:
                pass
        
        # Backend dependencies (Python)
        requirements = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements):
            try:
                with open(requirements) as f:
                    deps = [line.split("==")[0].strip() for line in f if line.strip() and not line.startswith("#")]
                    dependencies["backend"] = deps[:20]
                    dependencies["total_count"] += len(deps)
            except:
                pass
        
        return dependencies
    
    async def _analyze_code_metrics(self, repo_path: str) -> Dict:
        """Analyze code metrics"""
        metrics = {
            "lines_of_code": 0,
            "comment_lines": 0,
            "complexity_score": "N/A"
        }
        
        # Simple LOC counting
        code_extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb"]
        
        for root, _, files in os.walk(repo_path):
            if '.git' in root or 'node_modules' in root:
                continue
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            metrics["lines_of_code"] += len(lines)
                            metrics["comment_lines"] += sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
                    except:
                        pass
        
        return metrics
    
    async def _detect_architecture(self, repo_path: str) -> Dict:
        """Detect application architecture pattern"""
        architecture = {
            "pattern": "unknown",
            "features": []
        }
        
        # Check for common architecture patterns
        main_dirs = [d for d in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, d)) and not d.startswith('.')]
        
        if "frontend" in main_dirs and "backend" in main_dirs:
            architecture["pattern"] = "monorepo"
            architecture["features"].append("Full-stack monorepo")
        elif "src" in main_dirs and "public" in main_dirs:
            architecture["pattern"] = "spa"
            architecture["features"].append("Single Page Application")
        elif "api" in main_dirs or "routes" in main_dirs:
            architecture["pattern"] = "rest_api"
            architecture["features"].append("REST API")
        elif "services" in main_dirs or "microservices" in main_dirs:
            architecture["pattern"] = "microservices"
            architecture["features"].append("Microservices")
        
        return architecture
    
    def _analyze_documentation(self, repo_path: str) -> Dict:
        """Analyze project documentation"""
        docs = {
            "has_readme": False,
            "has_contributing": False,
            "has_license": False,
            "doc_files": []
        }
        
        files = os.listdir(repo_path)
        
        docs["has_readme"] = any("readme" in f.lower() for f in files)
        docs["has_contributing"] = any("contributing" in f.lower() for f in files)
        docs["has_license"] = any("license" in f.lower() for f in files)
        
        doc_files = [f for f in files if f.endswith((".md", ".txt", ".rst"))]
        docs["doc_files"] = doc_files
        
        return docs
    
    async def _analyze_security(self, repo_path: str) -> Dict:
        """Analyze security aspects"""
        security = {
            "has_gitignore": False,
            "exposed_secrets": [],
            "security_files": []
        }
        
        security["has_gitignore"] = os.path.exists(os.path.join(repo_path, ".gitignore"))
        
        # Check for security-related files
        files = os.listdir(repo_path)
        security_keywords = ["security", "cve", "audit"]
        security["security_files"] = [f for f in files if any(kw in f.lower() for kw in security_keywords)]
        
        return security
    
    def _calculate_quality_score(self, analysis: Dict) -> int:
        """Calculate repository quality score"""
        score = 50  # Base score
        
        # Documentation bonus
        if analysis.get("documentation", {}).get("has_readme"):
            score += 10
        if analysis.get("documentation", {}).get("has_license"):
            score += 5
        
        # Security bonus
        if analysis.get("security", {}).get("has_gitignore"):
            score += 5
        
        # Tech stack bonus
        if len(analysis.get("tech_stack", {}).get("devops", [])) > 0:
            score += 10
        
        # Code metrics bonus
        loc = analysis.get("code_metrics", {}).get("lines_of_code", 0)
        if loc > 1000:
            score += 10
        
        return min(100, max(0, score))
    
    def _detect_frontend_tech(self, html_content: str, headers: Dict) -> Dict:
        """Detect frontend technologies from HTML"""
        tech = {
            "frameworks": [],
            "libraries": []
        }
        
        html_lower = html_content.lower()
        
        if "react" in html_lower or "__react" in html_lower:
            tech["frameworks"].append("React")
        if "vue" in html_lower or "vue.js" in html_lower:
            tech["frameworks"].append("Vue.js")
        if "angular" in html_lower or "ng-" in html_lower:
            tech["frameworks"].append("Angular")
        if "next.js" in html_lower or "next/script" in html_lower:
            tech["frameworks"].append("Next.js")
        
        # Check headers
        server = headers.get("Server", "")
        if "nginx" in server.lower():
            tech["libraries"].append("Nginx")
        
        return tech
    
    def _analyze_security_headers(self, headers: Dict) -> Dict:
        """Analyze HTTP security headers"""
        security_headers = {
            "score": 0,
            "missing": [],
            "present": []
        }
        
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-XSS-Protection"
        ]
        
        for header in required_headers:
            if header in headers:
                security_headers["present"].append(header)
                security_headers["score"] += 20
            else:
                security_headers["missing"].append(header)
        
        return security_headers
    
    async def _llm_analyze_webapp(self, url: str, html_content: str) -> Dict:
        """Use LLM to analyze web application"""
        
        prompt = f"""Analyze this web application:

URL: {url}
HTML snippet (first 5000 chars):
{html_content}

Identify:
1. Application purpose
2. Main features visible
3. Technology stack indicators
4. User interface patterns
5. Potential improvements

Return JSON format:
{{
  "purpose": "...",
  "features": ["..."],
  "tech_indicators": ["..."],
  "ui_patterns": ["..."],
  "improvements": ["..."]
}}"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"purpose": "Unknown", "features": [], "tech_indicators": [], "ui_patterns": [], "improvements": []}
    
    def _detect_api_type(self, response) -> str:
        """Detect API documentation type"""
        content_type = response.headers.get("content-type", "").lower()
        text = response.text.lower()
        
        if "swagger" in text or "openapi" in text:
            return "OpenAPI/Swagger"
        elif "graphql" in text:
            return "GraphQL"
        elif "redoc" in text:
            return "ReDoc"
        elif content_type.startswith("application/json"):
            return "REST API"
        else:
            return "Unknown"
    
    async def _detect_deployment_platform(self, url: str) -> Dict:
        """Detect deployment platform"""
        platform = {
            "type": "unknown",
            "indicators": []
        }
        
        try:
            response = requests.head(url, timeout=10)
            headers = response.headers
            
            if "vercel" in headers.get("server", "").lower():
                platform["type"] = "Vercel"
            elif "netlify" in headers.get("server", "").lower():
                platform["type"] = "Netlify"
            elif "cloudflare" in headers.get("server", "").lower():
                platform["type"] = "Cloudflare"
            elif "aws" in str(headers).lower():
                platform["type"] = "AWS"
            
            platform["indicators"] = list(headers.keys())[:10]
        except:
            pass
        
        return platform
    
    def _sanitize_connection_string(self, conn_str: str) -> str:
        """Remove sensitive data from connection string"""
        import re
        # Remove password
        conn_str = re.sub(r':([^@:]+)@', ':****@', conn_str)
        return conn_str
    
    def _detect_db_type(self, connection_string: str) -> str:
        """Detect database type from connection string"""
        conn_lower = connection_string.lower()
        
        if "mongodb" in conn_lower:
            return "mongodb"
        elif "postgresql" in conn_lower or "postgres" in conn_lower:
            return "postgresql"
        elif "mysql" in conn_lower:
            return "mysql"
        elif "redis" in conn_lower:
            return "redis"
        else:
            return "unknown"
    
    async def _explore_mongodb(self, connection_string: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore MongoDB database"""
        analysis = {
            "database_type": "MongoDB",
            "collections": [],
            "indexes": {},
            "statistics": {}
        }
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            client = AsyncIOMotorClient(connection_string)
            db_name = connection_string.split("/")[-1].split("?")[0]
            db = client[db_name]
            
            # List collections
            collections = await db.list_collection_names()
            analysis["collections"] = collections
            
            # Get statistics for each collection
            for coll_name in collections[:5]:  # Limit to 5
                coll = db[coll_name]
                count = await coll.count_documents({})
                indexes = await coll.list_indexes().to_list(length=None)
                
                analysis["indexes"][coll_name] = [idx["name"] for idx in indexes]
                analysis["statistics"][coll_name] = {"document_count": count}
            
            client.close()
            
        except Exception as e:
            analysis["error"] = f"MongoDB exploration failed: {str(e)}"
        
        return analysis
    
    async def _explore_postgresql(self, connection_string: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore PostgreSQL database"""
        analysis = {
            "database_type": "PostgreSQL",
            "tables": [],
            "schemas": []
        }
        
        # Note: Would require asyncpg library
        analysis["message"] = "PostgreSQL exploration requires asyncpg library (to be implemented)"
        return analysis
    
    async def _explore_mysql(self, connection_string: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore MySQL database"""
        analysis = {
            "database_type": "MySQL",
            "tables": [],
            "schemas": []
        }
        
        analysis["message"] = "MySQL exploration requires aiomysql library (to be implemented)"
        return analysis
    
    async def _detect_bigdata_platform(self, platform_url: str, credentials: Optional[Dict]) -> str:
        """Detect big data platform type"""
        
        # Try to detect from URL or API
        if "kafka" in platform_url.lower():
            return "kafka"
        elif "hadoop" in platform_url.lower():
            return "hadoop"
        elif "spark" in platform_url.lower():
            return "spark"
        elif ":9200" in platform_url or "elasticsearch" in platform_url.lower():
            return "elasticsearch"
        
        return "generic"
    
    async def _explore_kafka(self, platform_url: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore Apache Kafka"""
        return {
            "topics": [],
            "consumer_groups": [],
            "message": "Kafka exploration requires kafka-python library (to be implemented)"
        }
    
    async def _explore_hadoop(self, platform_url: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore Hadoop cluster"""
        return {
            "hdfs_status": {},
            "yarn_applications": [],
            "message": "Hadoop exploration requires hdfs library (to be implemented)"
        }
    
    async def _explore_spark(self, platform_url: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore Apache Spark"""
        return {
            "applications": [],
            "executors": [],
            "message": "Spark exploration requires pyspark library (to be implemented)"
        }
    
    async def _explore_elasticsearch(self, platform_url: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Explore Elasticsearch"""
        analysis = {
            "cluster_health": {},
            "indices": [],
            "statistics": {}
        }
        
        try:
            # Get cluster health
            resp = requests.get(f"{platform_url}/_cluster/health", timeout=10)
            if resp.status_code == 200:
                analysis["cluster_health"] = resp.json()
            
            # List indices
            resp = requests.get(f"{platform_url}/_cat/indices?format=json", timeout=10)
            if resp.status_code == 200:
                indices = resp.json()
                analysis["indices"] = [idx["index"] for idx in indices]
                analysis["statistics"] = {
                    "total_indices": len(indices),
                    "total_docs": sum(int(idx.get("docs.count", 0)) for idx in indices)
                }
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    async def _generic_bigdata_analysis(self, platform_url: str, credentials: Optional[Dict], task_id: Optional[str]) -> Dict:
        """Generic big data platform analysis"""
        return {
            "platform_url": platform_url,
            "message": "Generic big data platform detected. Specific analysis not available."
        }
    
    async def _generate_recommendations(self, analysis: Dict, target_type: str) -> List[Dict]:
        """Generate enhancement recommendations"""
        
        recommendations_prompt = f"""Based on this {target_type} analysis, generate improvement recommendations:

Analysis:
{json.dumps(analysis, indent=2)[:3000]}

Generate 5-10 specific, actionable recommendations.
Prioritize by impact.

Return JSON array:
[
  {{
    "priority": "high/medium/low",
    "category": "...",
    "title": "...",
    "description": "...",
    "impact": "..."
  }}
]"""

        try:
            response = await self.llm_client.ainvoke([HumanMessage(content=recommendations_prompt)])
            import re
            json_match = re.search(r'\[[\s\S]*\]', response.content)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return [{
            "priority": "medium",
            "category": "general",
            "title": "Review analysis results",
            "description": "Manually review the exploration results and implement improvements",
            "impact": "Improves overall system quality"
        }]
    
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


def get_explorer_agent(llm_client, db, manager, file_service) -> ExplorerAgent:
    """Get ExplorerAgent instance"""
    return ExplorerAgent(llm_client, db, manager, file_service)
