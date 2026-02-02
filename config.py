"""Configuration for the Project Researcher Agent."""

from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent
RESEARCH_DIR = PROJECT_ROOT / "research"
TOPICS_DIR = RESEARCH_DIR / "topics"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Research settings
MAX_SEARCH_RESULTS = 10
MAX_SOURCES_TO_FETCH = 5

# Ensure directories exist
TOPICS_DIR.mkdir(parents=True, exist_ok=True)
