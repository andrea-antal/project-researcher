# Research Methodology - Core Reference

This file contains the core research methodology principles. The main SKILL.md file contains the full workflow.

## Research Approach

1. **Clarify First**: Ask 2-3 focused questions to understand:
   - Specific aspects the user cares about
   - Depth needed (quick overview vs. comprehensive analysis)
   - Any constraints or preferences

2. **Research Systematically**:
   - Apply the Source Trust Hierarchy (domain-specific)
   - Extract key information from each source
   - Look for comparisons, trade-offs, real-world evidence
   - Cross-reference claims across multiple independent sources

3. **Synthesize Findings**:
   - Create structured summaries with clear sections
   - Build comparison tables when comparing options
   - Highlight trade-offs and recommendations
   - Note gaps, uncertainties, areas needing more research

4. **Persist Knowledge**:
   - Save detailed notes to the local knowledge base
   - Include source URLs for reference
   - Structure notes for easy follow-up queries

## Parallel Research Strategy

For complex topics, decompose into parallel research threads:

1. **Identify Angles**: Break topic into 3-5 independent aspects
2. **Launch Parallel**: Use Task tool to spawn sub-agents simultaneously
3. **Aggregate**: After completion, read outputs and synthesize

### When to Parallelize
- Topic has 3+ distinct aspects
- Aspects are independent (don't need each other's results)
- Complexity justifies coordination overhead

### When NOT to Parallelize
- Simple, focused topics
- Topics where one finding informs the next
- Quick overviews

## Output Structure

```
./output/topics/<topic-slug>/
├── overview.md      # Main summary
├── sources.md       # Source list with excerpts
└── notes/           # Detailed subtopic notes

./output/synthesis/
├── connections.md   # Cross-domain connections
├── patterns.md      # Recurring themes
├── tensions.md      # Conflicts and trade-offs
└── questions.md     # Open questions
```
