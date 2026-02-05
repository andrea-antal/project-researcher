# Research Skill

A structured research assistant that explores topics thoroughly and builds a local knowledge base.

## Usage

```
/research <topic>                    Start new research (auto-detects domain)
/research --domain=tech <topic>      Force specific domain (tech|policy|thought-leadership|general)
/research --parallel <topic>         Use parallel sub-agents for complex topics
/research --follow-up <topic-slug>   Continue existing research, ask follow-up questions
/research --synthesize               Cross-topic synthesis of all research
/research --list                     List all researched topics
```

## Workflow

### Phase 1: Parse Arguments

Extract from `{args}`:
- `--domain=X` -> force domain (tech, policy, thought-leadership, general)
- `--parallel` -> use parallel research threads
- `--follow-up <slug>` -> continue existing research
- `--synthesize` -> cross-topic synthesis mode
- `--list` -> list existing topics
- Remaining text -> research topic

### Phase 2: Route by Mode

**If --list:**
1. Use Glob to find `./output/topics/*/overview.md`
2. List topic names and first line of each overview
3. Done

**If --synthesize:**
1. Read `~/.claude/skills/research/prompts/synthesize.md`
2. Use Glob to find all `./output/topics/*/overview.md`
3. Read each overview
4. Follow synthesis prompt to produce cross-domain insights
5. Save to `./output/synthesis/` (connections.md, patterns.md, tensions.md, questions.md)
6. Done

**If --follow-up:**
1. Load existing research from `./output/topics/<slug>/`
2. Read overview.md and sources.md
3. Answer user's follow-up question with context
4. Append new findings to notes/ if substantial
5. Done

**If new research (default):**
Continue to Phase 3

### Phase 3: Domain Detection

If `--domain` not specified, classify the topic:

**Tech indicators:** programming, software, hardware, frameworks, libraries, APIs, databases, infrastructure, DevOps, cloud, ML/AI tools, benchmarks, debugging, architecture

**Policy indicators:** government, legislation, regulation, economics, tax, trade, political theory, rights, law, court, international relations, public policy, social programs

**Thought-leadership indicators:** "who are the experts", "leading thinkers", "influential voices", authorities, "who to follow", experts on, gurus, thought leaders, key figures

**General:** None of the above strongly indicated

Load the appropriate domain prompt from `~/.claude/skills/research/domains/{domain}.md`

### Phase 4: Clarifying Questions

Ask 2-3 focused clarifying questions based on:
- The topic's apparent scope
- Domain-specific considerations (from loaded prompt)
- What would help narrow vs. broaden research appropriately

Use direct text output (not AskUserQuestion tool) to ask questions.
Wait for user response before proceeding.

### Phase 5: Research Execution

**Standard mode:**
1. Use WebSearch to find relevant sources (3-5 searches with varied queries)
2. Apply source trust hierarchy from domain prompt to filter results
3. Use WebFetch to extract content from promising sources (prefer Tier 1-2)
4. Extract key information, noting source URLs
5. Cross-reference claims across multiple sources
6. Note any conflicting information or gaps

**Parallel mode (--parallel):**
1. Decompose topic into 3-5 independent research angles
2. Create a task for each angle using TaskCreate
3. Launch parallel sub-agents using Task tool with subagent_type="general-purpose"
   - Each agent: research one angle, save to `./output/topics/<slug>/notes/<angle>.md`
   - Launch ALL Task calls in a SINGLE message for true parallelism
4. Wait for all agents to complete
5. Read their outputs and synthesize

### Phase 6: Synthesis & Output

1. Synthesize findings into structured format:
   - **Overview**: What the topic is and why it matters
   - **Key Findings**: Main insights organized by theme
   - **Comparison Table**: When comparing options (side-by-side features)
   - **Recommendations**: Based on stated requirements (if applicable)
   - **Open Questions**: Gaps or uncertainties worth noting
   - **Sources**: URLs consulted with trust tier and brief descriptions

2. Create topic slug: lowercase, hyphens, no special chars (e.g., "react-state-management")

3. Save outputs:
   - `./output/topics/<slug>/overview.md` - Main summary
   - `./output/topics/<slug>/sources.md` - Source list with excerpts
   - `./output/topics/<slug>/notes/` - Detailed subtopic notes (if any)

4. Present summary to user with path to saved files

## Source Evaluation (Universal)

For every source, assess:

### Authority
- Who wrote this? Can you identify the author?
- What are their credentials for this topic?
- Is the publishing organization reputable?

### Accuracy
- Does it cite primary sources or provide evidence?
- Can claims be verified against other sources?
- Specific details or vague statements?

### Currency
- When was this published/updated?
- Is the information still relevant?
- How quickly does this field change?

### Purpose & Bias
- Informing, selling, or persuading?
- Conflict of interest?
- Are limitations acknowledged?

### Corroboration (Critical)
- Never rely on a single source for important claims
- Cross-reference across 2-3 independent sources
- Note disagreements and investigate why

## Red Flags - Do Not Trust

- No author attribution
- No dates or publication info
- Broken links, missing references
- Excessive ads, clickbait headlines
- Claims that can't be found anywhere else
- AI-generated filler content
- Content farms ranking for every keyword

## Guidelines

- Be direct and concise
- Prioritize accuracy over comprehensiveness
- Cite sources when making claims
- Acknowledge uncertainty when information conflicts
- Ask before spending significant time on tangential research
- For complex topics, suggest parallel mode if not already using it
