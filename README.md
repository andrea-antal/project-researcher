# Project Researcher Agent

An interactive research agent built with the Claude Agent SDK that helps explore topics, build knowledge bases, and answer follow-up questions.

## Features

- **Domain auto-detection**: Automatically applies appropriate research methodology
- **Interactive questioning**: Asks clarifying questions to understand research scope
- **Web research**: Searches and fetches content from relevant sources
- **Source vetting**: Applies domain-specific trust hierarchies
- **Knowledge persistence**: Saves structured notes to local files
- **Follow-up sessions**: Continue conversations using accumulated context
- **Cross-domain synthesis**: Find connections across all research topics
- **Cost tracking**: Reports API costs after each session

## Domains

The agent auto-detects which domain applies to your topic:

| Domain | Focus | Example Topics |
|--------|-------|----------------|
| `tech` | Software, tools, frameworks | MCP servers, React patterns, database optimization |
| `policy` | Political theory, economics, governance | UBI, trade policy, regulatory frameworks |
| `thought-leadership` | Finding and vetting leading thinkers | AI alignment experts, behavioral economics pioneers |
| `general` | Everything else | Historical events, scientific concepts |

Each domain has tailored source trust hierarchies and evaluation criteria.

## Source Vetting & Domain Filters

### How Domain Detection Works

When you submit a research topic, the agent uses Claude to classify it into one of the four domains above. Each domain then applies a tailored source trust hierarchy and evaluation criteria specific to that field.

### Four-Tier Trust Hierarchy

Every domain follows a consistent four-tier structure, with domain-specific examples:

| Tier | Trust Level | Description |
|------|-------------|-------------|
| **Tier 1** | Highest | Primary sources: official docs, peer-reviewed research, original works, source code |
| **Tier 2** | High | Verified secondary: established publications, expert analysis, institutional research |
| **Tier 3** | Moderate | Community sources: Stack Overflow, practitioner blogs, forum discussions - verify claims |
| **Tier 4** | Caution | Content farms, anonymous sources, outdated material, AI-generated filler |

#### Domain-Specific Examples

**Tech Domain:**
- Tier 1: Official project documentation, RFCs, source code, GitHub releases
- Tier 4: "Top 10 Best Frameworks" listicles, SEO-optimized aggregator sites

**Policy Domain:**
- Tier 1: Legislative text, CBO reports, peer-reviewed journals, foundational theorists
- Tier 4: Partisan media without fact-checking, anonymous policy blogs

**Thought Leadership:**
- Tier 1: Books and papers by the thinkers themselves, substantive long-form interviews
- Tier 4: Social media hot takes, promotional interviews, hagiographic profiles

**General:**
- Tier 1: Original research, official publications, peer-reviewed academic work
- Tier 4: Content farms, unattributed content, promotional material disguised as information

### Universal Evaluation Criteria

Regardless of domain, every source is assessed on five dimensions:

1. **Authority**: Author credentials, publishing organization reputation, relevant expertise
2. **Accuracy**: Evidence cited, claims verifiable, specific details vs vague statements, corroborated by other sources
3. **Currency**: Publication date, relevance to current context, how fast the field changes
4. **Purpose & Bias**: Informing vs. selling vs. persuading, conflicts of interest, tone balance
5. **Corroboration**: Never rely on a single source for important claims - cross-reference across 2-3 independent sources

### Red Flags (Automatic Rejection)

Sources exhibiting these characteristics are not used:

- No author attribution
- No dates or publication info
- Broken links, missing references
- Excessive ads, clickbait headlines
- Claims that can't be found anywhere else
- Content that reads like AI-generated filler without citations
- Sites that rank for every possible keyword (content farms)
- SEO-optimized listicles ("Top 10 Best...")

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
./research
```

Commands:
- `research <topic>` - Start new research
- `follow <topic>` - Continue with follow-up questions
- `synthesize` - Find connections across all topics
- `quit` - Exit

### Command Line

```bash
# Start research on a topic
./research "Compare MCP servers for Postgres access"

# Continue with follow-up questions
./research follow "mcp-servers"

# Synthesize insights across all research
./research synthesize
```

## Knowledge Base Structure

Research is saved to `output/topics/{topic-slug}/`:

```
output/
├── index.md              # Topic index
├── topics/
│   └── {topic-slug}/
│       ├── overview.md   # Main summary and recommendations
│       ├── sources.md    # Source URLs with key excerpts
│       └── notes/        # Detailed subtopic notes
└── synthesis/
    ├── connections.md    # Cross-domain connections
    ├── patterns.md       # Recurring themes
    ├── tensions.md       # Conflicts and trade-offs
    └── questions.md      # Open questions raised
```

## Example Session

```
>>> research Who are the leading thinkers on AI alignment

[Detecting domain...]
[Domain: thought-leadership]

============================================================
Research Topic: Who are the leading thinkers on AI alignment
Domain: thought-leadership
Output Directory: output/topics/who-are-the-leading-thinkers-on-ai-align
============================================================

I'd like to understand your needs better before researching:

1. What's your primary interest?
   - Academic researchers and their theoretical contributions
   - Industry practitioners working on practical solutions
   - Public intellectuals shaping the discourse
   - All of the above for a comprehensive landscape

2. What depth are you looking for?
   - Quick overview of key figures
   - Deep dive including their core arguments and critiques
   - Mapping of different schools of thought and their proponents

[Searching: AI alignment researchers prominent...]
[Fetching: https://80000hours.org/...]
[Saving: overview.md...]

============================================================
Research complete!
Notes saved to: output/topics/who-are-the-leading-thinkers-on-ai-align
Cost: $0.0341
============================================================
```

## Prompts Structure

```
prompts/
├── core.md                    # Universal research methodology
├── synthesize.md              # Cross-domain synthesis instructions
└── domains/
    ├── tech.md                # Tech source hierarchy & evaluation
    ├── policy.md              # Policy source hierarchy & evaluation
    ├── thought-leadership.md  # Expert vetting framework
    └── general.md             # Fallback for other topics
```

## Configuration

Edit `config.py` to customize:

- `RESEARCH_DIR`: Where to save research notes
- `MAX_SEARCH_RESULTS`: Number of search results to consider
- `MAX_SOURCES_TO_FETCH`: Sources to fetch per search
