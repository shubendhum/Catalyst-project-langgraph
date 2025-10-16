#!/usr/bin/env python3
"""
Environment File Generator for Catalyst Platform
Generates .env files for backend and frontend from config.yaml
"""

import yaml
import os
from pathlib import Path

def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_backend_env(config, output_path='backend/.env'):
    """Generate backend .env file"""
    
    # Build MongoDB URL with auth
    mongo_url = f"mongodb://{config['database']['root_username']}:{config['database']['root_password']}@mongodb:27017"
    
    env_lines = [
        "# Catalyst Backend Environment Variables",
        "# Auto-generated from config.yaml",
        "",
        "# Database Configuration",
        f"MONGO_URL={mongo_url}",
        f"DB_NAME={config['database']['name']}",
        "",
        "# API Configuration",
        f"CORS_ORIGINS={config['backend']['cors_origins']}",
        f"LOG_LEVEL={config['backend']['log_level']}",
        "",
        "# LLM Integration",
        f"EMERGENT_LLM_KEY={config['llm']['emergent_llm_key']}",
        f"DEFAULT_LLM_PROVIDER={config['llm']['default_provider']}",
        f"DEFAULT_LLM_MODEL={config['llm']['default_model']}",
        "",
        "# Explorer Agent (Optional)",
        f"GITHUB_TOKEN={config['explorer'].get('github_token', '')}",
        f"JIRA_URL={config['explorer'].get('jira_url', '')}",
        f"JIRA_USERNAME={config['explorer'].get('jira_username', '')}",
        f"JIRA_API_TOKEN={config['explorer'].get('jira_api_token', '')}",
        f"SERVICENOW_URL={config['explorer'].get('servicenow_url', '')}",
        f"SERVICENOW_USERNAME={config['explorer'].get('servicenow_username', '')}",
        f"SERVICENOW_PASSWORD={config['explorer'].get('servicenow_password', '')}",
        "",
        "# Security",
        f"ENABLE_AUDIT_LOGS={str(config['security']['enable_audit_logs']).lower()}",
        f"ENABLE_PII_REDACTION={str(config['security']['enable_pii_redaction']).lower()}",
        f"SESSION_TIMEOUT={config['security']['session_timeout']}",
        "",
        "# Performance",
        f"MAX_CONCURRENT_TASKS={config['performance']['max_concurrent_tasks']}",
        f"AGENT_TIMEOUT={config['performance']['agent_timeout']}",
        f"WEBSOCKET_PING_INTERVAL={config['performance']['websocket_ping_interval']}",
        "",
        "# Monitoring",
        f"ENABLE_METRICS={str(config['monitoring']['enable_metrics']).lower()}",
        f"ENABLE_PERFORMANCE_MONITORING={str(config['monitoring']['enable_performance_monitoring']).lower()}",
        f"SENTRY_DSN={config['monitoring']['sentry_dsn']}",
        "",
        "# Deployment",
        f"ENVIRONMENT={config['deployment']['environment']}",
        f"MOCK_DEPLOYMENT={str(config['deployment']['mock_deployment']).lower()}",
        ""
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✓ Generated {output_path}")

def generate_frontend_env(config, output_path='frontend/.env'):
    """Generate frontend .env file"""
    
    env_lines = [
        "# Catalyst Frontend Environment Variables",
        "# Auto-generated from config.yaml",
        "",
        "# Backend API URL",
        f"REACT_APP_BACKEND_URL={config['frontend']['backend_url']}",
        "",
        "# Development Settings",
        "WDS_SOCKET_PORT=443",
        f"REACT_APP_ENABLE_VISUAL_EDITS={str(config['frontend']['enable_visual_edits']).lower()}",
        f"ENABLE_HEALTH_CHECK={str(config['frontend']['enable_health_check']).lower()}",
        ""
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✓ Generated {output_path}")

def generate_root_env(config, output_path='.env'):
    """Generate root .env file for docker-compose"""
    
    env_lines = [
        "# Catalyst Platform Environment Variables",
        "# Used by docker-compose.yml",
        "# Auto-generated from config.yaml",
        "",
        "# Database Configuration",
        f"MONGO_ROOT_USERNAME={config['database']['root_username']}",
        f"MONGO_ROOT_PASSWORD={config['database']['root_password']}",
        f"DB_NAME={config['database']['name']}",
        f"MONGO_PORT={config['database']['port']}",
        "",
        "# Service Ports",
        f"BACKEND_PORT={config['backend']['port']}",
        f"FRONTEND_PORT={config['frontend']['port']}",
        "",
        "# LLM Configuration",
        f"EMERGENT_LLM_KEY={config['llm']['emergent_llm_key']}",
        "",
        "# CORS",
        f"CORS_ORIGINS={config['backend']['cors_origins']}",
        ""
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✓ Generated {output_path}")

if __name__ == '__main__':
    # Check if config.yaml exists
    if not os.path.exists('config.yaml'):
        print("✗ Error: config.yaml not found")
        print("  Please create config.yaml first")
        exit(1)
    
    # Load config
    try:
        config = load_config()
        
        # Generate all env files
        generate_root_env(config)
        generate_backend_env(config)
        generate_frontend_env(config)
        
        print("\n✓ All environment files generated successfully!")
        print("\n⚠ IMPORTANT: Review the generated .env files and update:")
        print("  1. EMERGENT_LLM_KEY (required)")
        print("  2. MONGO_ROOT_PASSWORD (for production)")
        print("  3. CORS_ORIGINS (for production)")
        print("  4. REACT_APP_BACKEND_URL (for production)")
        print("\nFiles generated:")
        print("  - .env (root - for docker-compose)")
        print("  - backend/.env (backend configuration)")
        print("  - frontend/.env (frontend configuration)")
        
    except Exception as e:
        print(f"✗ Error generating .env files: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)