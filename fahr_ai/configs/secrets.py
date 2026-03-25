# config.py

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Configuration file paths
ORCHESTRATOR_CONFIG_PATH = os.path.join(BASE_DIR, "orchestrator_configs.yaml")
AGENTS_CONFIG_PATH = os.path.join(BASE_DIR, "agents_config.yaml")
ROLE_AGENT_MAPPING_PATH = os.path.join(BASE_DIR, "role_management/role_agent_map.json")
ROLE_API_MAPPING_PATH = os.path.join(BASE_DIR, "role_management/role_api_map.json")

CRM_API_BASE_URL = "http://10.254.115.17:8090"
