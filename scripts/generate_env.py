#!/usr/bin/env python3
"""
Environment File Generator for Catalyst Platform
Generates .env file from config.yaml
"""

import yaml
import os
from pathlib import Path

def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_env_file(config, output_path='.env'):
    """Generate .env file from config dictionary"""
    env_lines = [
        "# Catalyst Platform Environment Variables",
        "# Generated from config.yaml",
        "# Edit this file to customize your deployment",
        "",
        "# ======================",
        "# Database Configuration",
        "# ======================",
        f"MONGO_ROOT_USERNAME={config['database']['root_username']}",
        f"MONGO_ROOT_PASSWORD={config['database']['root_password']}",
        f"DB_NAME={config['database']['name']}",
        f"MONGO_PORT={config['database']['port']}",
        f"MONGO_URL={config['database']['url']}",
        "",
        "# ======================",
        "# Backend Configuration",
        "# ======================",
        f"BACKEND_PORT={config['backend']['port']}",
        f"CORS_ORIGINS={config['backend']['cors_origins']}",
        f"LOG_LEVEL={config['backend']['log_level']}",
        "",
        "# ======================",
        "# Frontend Configuration",
        "# ======================",
        f"FRONTEND_PORT={config['frontend']['port']}",
        f"REACT_APP_BACKEND_URL={config['frontend']['backend_url']}",
        f"REACT_APP_ENABLE_VISUAL_EDITS={str(config['frontend']['enable_visual_edits']).lower()}",
        f"ENABLE_HEALTH_CHECK={str(config['frontend']['enable_health_check']).lower()}",
        "",
        "# ======================",
        "# LLM Configuration",
        "# ======================",
        f"EMERGENT_LLM_KEY={config['llm']['emergent_llm_key']}",
        f"DEFAULT_LLM_PROVIDER={config['llm']['default_provider']}",
        f"DEFAULT_LLM_MODEL={config['llm']['default_model']}",
        "",
        "# Optional: Specific provider keys (comment out if using Emergent key)",
        "# OPENAI_API_KEY=your_openai_key",
        "# ANTHROPIC_API_KEY=your_anthropic_key",
        "# GOOGLE_API_KEY=your_google_key",
        "",
        "# ======================",
        "# Explorer Agent (Optional)",
        "# ======================",
        f"GITHUB_TOKEN={config['explorer'].get('github_token', '')}",
        f"JIRA_URL={config['explorer'].get('jira_url', '')}",
        f"JIRA_USERNAME={config['explorer'].get('jira_username', '')}",
        f"JIRA_API_TOKEN={config['explorer'].get('jira_api_token', '')}",
        f"SERVICENOW_URL={config['explorer'].get('servicenow_url', '')}",
        f"SERVICENOW_USERNAME={config['explorer'].get('servicenow_username', '')}",
        f"SERVICENOW_PASSWORD={config['explorer'].get('servicenow_password', '')}",
        "",
        "# ======================",
        "# Deployment Configuration",
        "# ======================",
        f"ENVIRONMENT={config['deployment']['environment']}",
        f"MOCK_DEPLOYMENT={str(config['deployment']['mock_deployment']).lower()}",
        f"DEPLOYMENT_PROVIDER={config['deployment']['provider']}",
        "",
        "# ======================",
        "# Security Configuration",
        "# ======================",
        f"ENABLE_AUDIT_LOGS={str(config['security']['enable_audit_logs']).lower()}",
        f"ENABLE_PII_REDACTION={str(config['security']['enable_pii_redaction']).lower()}",
        f"SESSION_TIMEOUT={config['security']['session_timeout']}",
        "",
        "# ======================",
        "# Performance Configuration",
        "# ======================",
        f"MAX_CONCURRENT_TASKS={config['performance']['max_concurrent_tasks']}",
        f"AGENT_TIMEOUT={config['performance']['agent_timeout']}",
        f"WEBSOCKET_PING_INTERVAL={config['performance']['websocket_ping_interval']}",
        "",
        "# ======================",
        "# Monitoring Configuration",
        "# ======================",
        f"ENABLE_METRICS={str(config['monitoring']['enable_metrics']).lower()}",
        f"ENABLE_PERFORMANCE_MONITORING={str(config['monitoring']['enable_performance_monitoring']).lower()}",
        f"SENTRY_DSN={config['monitoring']['sentry_dsn']}",
        ""
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✓ Generated {output_path}")
    print("\n⚠ IMPORTANT: Edit .env and add your EMERGENT_LLM_KEY before starting the platform")

if __name__ == '__main__':
    # Check if config.yaml exists
    if not os.path.exists('config.yaml'):
        print("✗ Error: config.yaml not found")
        print("  Please create config.yaml first")
        exit(1)
    
    # Load config and generate .env
    try:
        config = load_config()
        generate_env_file(config)
        print("\n✓ Environment file generated successfully!")
    except Exception as e:
        print(f"✗ Error generating .env file: {str(e)}")
        exit(1)