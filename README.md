# Project Researcher Agent

An interactive research agent built with the Claude Agent SDK that helps explore topics, build knowledge bases, and answer follow-up questions.

## Features

- **Interactive questioning**: Asks clarifying questions to understand research scope
- **Web research**: Searches and fetches content from relevant sources
- **Knowledge persistence**: Saves structured notes to local files
- **Follow-up sessions**: Continue conversations using accumulated context
- **Cost tracking**: Reports API costs after each session

## Installation

```bash
cd project-researcher
pip install -r requirements.txt
```

Requires:
- Python 3.10+
- Claude Agent SDK (`pip install claude-agent-sdk`)
- Claude Code CLI (bundled with SDK)

## Usage

### Interactive Mode

```bash
python agent.py
```

Commands:
- `research <topic>` - Start new research
- `follow <topic>` - Continue with follow-up questions
- `quit` - Exit

### Command Line

```bash
# Start research on a topic
python agent.py "Compare MCP servers for Postgres access"

# Continue with follow-up questions
python agent.py follow "mcp-servers"
```

## Knowledge Base Structure

Research is saved to `research/topics/{topic-slug}/`:

```
research/
├── index.md              # Topic index
└── topics/
    └── {topic-slug}/
        ├── overview.md   # Main summary and recommendations
        ├── sources.md    # Source URLs with key excerpts
        └── notes/        # Detailed subtopic notes
```

## Example Session

```
>>> research Compare MCP servers for Postgres access

============================================================
Research Topic: Compare MCP servers for Postgres access
Output Directory: research/topics/compare-mcp-servers-for-postgres-access
============================================================

I'd like to understand your needs better before researching:

1. What's your primary use case?
   - Read-only queries and analysis
   - Full CRUD operations
   - Schema inspection and management

2. What environment are you working in?
   - Local development
   - Production server
   - Cloud-hosted database

[Searching: MCP servers Postgres database integration...]
[Fetching: https://github.com/modelcontextprotocol/servers...]
[Saving: overview.md...]

============================================================
Research complete!
Notes saved to: research/topics/compare-mcp-servers-for-postgres-access
Cost: $0.0234
============================================================
```

## Configuration

Edit `config.py` to customize:

- `RESEARCH_DIR`: Where to save research notes
- `MAX_SEARCH_RESULTS`: Number of search results to consider
- `MAX_SOURCES_TO_FETCH`: Sources to fetch per search
