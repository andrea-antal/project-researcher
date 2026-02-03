"""Configuration for the Project Researcher Agent."""

from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent
RESEARCH_DIR = PROJECT_ROOT / "output"
TOPICS_DIR = RESEARCH_DIR / "topics"
SYNTHESIS_DIR = RESEARCH_DIR / "synthesis"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DOMAINS_DIR = PROMPTS_DIR / "domains"

# Research settings
MAX_SEARCH_RESULTS = 10
MAX_SOURCES_TO_FETCH = 5

# Available domains
DOMAINS = ["tech", "policy", "thought-leadership", "general"]

# Ensure directories exist
TOPICS_DIR.mkdir(parents=True, exist_ok=True)
SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)
