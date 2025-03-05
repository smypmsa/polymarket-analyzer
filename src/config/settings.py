from typing import Dict, Any
from pathlib import Path
import os

# API Settings
POLYMARKET_BASE_URL = "https://clob.polymarket.com"
DEFAULT_REQUEST_TIMEOUT = 30

# Storage Settings
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "markets"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# OpenRouter Settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.7-sonnet"
DEFAULT_TEMPERATURE = 0.1

# Analysis Output Directory
ANALYSIS_DIR = Path(__file__).parent.parent.parent / "data" / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)