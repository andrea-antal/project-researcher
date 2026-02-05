#!/usr/bin/env python3
"""
Project Researcher Agent

An interactive research agent that:
1. Takes a research topic
2. Auto-detects the appropriate domain (tech, policy, thought-leadership, general)
3. Asks clarifying questions to understand scope
4. Searches the web for relevant sources
5. Extracts and synthesizes information
6. Builds a local knowledge base
7. Answers follow-up questions using accumulated context
8. Synthesizes insights across all research topics
"""

import re
import sys
import time
from pathlib import Path

import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from config import PROMPTS_DIR, TOPICS_DIR, SYNTHESIS_DIR, DOMAINS_DIR, DOMAINS


# Define sub-agent types for parallel research threads
RESEARCH_AGENTS = {
    "research-thread": AgentDefinition(
        description="Research a specific angle or subtopic thoroughly",
        prompt="""You are a focused research agent. Research your assigned angle thoroughly:
1. Search for authoritative sources
2. Fetch and extract key information
3. Save findings to your assigned output file
4. Be thorough but focused on your specific angle only""",
        tools=["WebSearch", "WebFetch", "Read", "Write"],
        model="sonnet",
    ),
    "source-validator": AgentDefinition(
        description="Validate and vet sources for credibility",
        prompt="""You validate sources for research quality:
1. Check author credentials
2. Verify publication date and currency
3. Cross-reference claims
4. Rate source reliability""",
        tools=["WebSearch", "WebFetch", "Read"],
        model="haiku",
    ),
}


class ToolProgressTracker:
    """Track tool execution progress with timestamps and timeout warnings."""

    SLOW_THRESHOLD = 30  # seconds before showing "still working..."

    def __init__(self):
        self.current_tool: str | None = None
        self.current_detail: str = ""
        self.start_time: float | None = None
        self._warning_task: anyio.abc.TaskGroup | None = None
        self._cancel_scope: anyio.CancelScope | None = None

    def _timestamp(self) -> str:
        """Get current timestamp string."""
        return time.strftime("%H:%M:%S")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        else:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"

    def start(self, tool_name: str, detail: str = "") -> None:
        """Record that a tool has started."""
        # Complete previous tool if any
        self.complete()

        self.current_tool = tool_name
        self.current_detail = detail
        self.start_time = time.time()

        detail_str = f": {detail}" if detail else ""
        print(f"[{self._timestamp()}] {tool_name}{detail_str}...")

    def complete(self) -> None:
        """Mark current tool as complete."""
        if self.current_tool and self.start_time:
            duration = time.time() - self.start_time
            duration_str = self._format_duration(duration)
            print(f"[{self._timestamp()}] {self.current_tool} complete ({duration_str})")

        self.current_tool = None
        self.current_detail = ""
        self.start_time = None

    def check_slow(self) -> None:
        """Check if current operation is slow and print warning."""
        if self.current_tool and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.SLOW_THRESHOLD:
                print(f"[{self._timestamp()}] Still working on {self.current_tool}... ({self._format_duration(elapsed)} elapsed)")


# Global tracker instance
_tracker = ToolProgressTracker()


def load_prompt(filename: str) -> str:
    """Load a prompt file."""
    prompt_file = PROMPTS_DIR / filename
    if prompt_file.exists():
        return prompt_file.read_text()
    return ""


def load_domain_prompt(domain: str) -> str:
    """Load the domain-specific prompt."""
    domain_file = DOMAINS_DIR / f"{domain}.md"
    if domain_file.exists():
        return domain_file.read_text()
    return load_domain_prompt("general")


def build_system_prompt(domain: str) -> str:
    """Build the full system prompt from core + domain."""
    core = load_prompt("core.md")
    domain_prompt = load_domain_prompt(domain)
    return f"{core}\n\n---\n\n{domain_prompt}"


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:50]


def get_topic_dir(topic: str) -> Path:
    """Get or create the directory for a research topic."""
    slug = slugify(topic)
    topic_dir = TOPICS_DIR / slug
    topic_dir.mkdir(parents=True, exist_ok=True)
    (topic_dir / "notes").mkdir(exist_ok=True)
    return topic_dir


async def detect_domain(topic: str) -> str:
    """Use Claude to detect the appropriate domain for a topic."""
    detection_prompt = f"""Classify this research topic into exactly one domain.

Topic: {topic}

Domains:
- tech: Software, programming, tools, frameworks, technical systems, developer topics
- policy: Political theory, economics, governance, regulations, public policy, social policy
- thought-leadership: Finding and vetting leading thinkers, experts, influential voices on any topic
- general: Everything else that doesn't fit the above

Respond with ONLY the domain name (tech, policy, thought-leadership, or general), nothing else."""

    options = ClaudeAgentOptions(
        system_prompt="You are a classifier. Respond only with the requested classification.",
        allowed_tools=[],
        max_turns=1,
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(detection_prompt)
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        domain = block.text.strip().lower()
                        if domain in DOMAINS:
                            return domain
            elif isinstance(message, ResultMessage):
                break

    return "general"


async def research(topic: str, domain: str | None = None) -> None:
    """Run the research agent on a topic."""
    topic_dir = get_topic_dir(topic)

    # Auto-detect domain if not specified
    if domain is None:
        print("[Detecting domain...]")
        domain = await detect_domain(topic)
        print(f"[Domain: {domain}]")

    system_prompt = build_system_prompt(domain)

    print(f"\n{'=' * 60}")
    print(f"Research Topic: {topic}")
    print(f"Domain: {domain}")
    print(f"Output Directory: {topic_dir}")
    print(f"{'=' * 60}\n")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "Read",
            "Write",
            "Glob",
            "Grep",
            "Task",
            "TodoWrite",
        ],
        agents=RESEARCH_AGENTS,
        max_turns=50,
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        # Phase 1: Get clarifying questions
        clarify_prompt = f"""Research topic: {topic}

Before researching, ask 2-3 clarifying questions to understand:
- What specific aspects matter most
- Desired depth (quick overview vs comprehensive)
- Any constraints or preferences

Output your questions as a numbered list. Do not start researching yet."""

        await client.query(clarify_prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                print()

        # Phase 2: Get user's answers
        print("\n" + "-" * 40)
        print("Answer the questions above (or press Enter to skip):")
        print("-" * 40)
        try:
            user_answers = input("\nYour answers: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nResearch cancelled.")
            return

        # Phase 3: Do the research with user context
        research_prompt = f"""Now research the topic: {topic}

User's clarifications: {user_answers if user_answers else "No specific preferences - use your judgment."}

Save your findings to: {topic_dir}
- overview.md: Main summary and recommendations
- sources.md: List of sources with key excerpts
- notes/: Detailed notes on subtopics

Proceed with the research."""

        await client.query(research_prompt)

        tracker = ToolProgressTracker()
        last_check = time.time()

        async for message in client.receive_messages():
            # Check for slow operations periodically
            now = time.time()
            if now - last_check > 10:
                tracker.check_slow()
                last_check = now

            if isinstance(message, AssistantMessage):
                # Complete any pending tool before showing text
                tracker.complete()

                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.name
                        if tool_name == "WebSearch":
                            query = block.input.get("query", "")
                            tracker.start("Search", query)
                        elif tool_name == "WebFetch":
                            url = block.input.get("url", "")
                            # Truncate long URLs
                            display_url = url if len(url) < 60 else url[:57] + "..."
                            tracker.start("Fetch", display_url)
                        elif tool_name == "Write":
                            path = block.input.get("file_path", "")
                            filename = Path(path).name
                            tracker.start("Save", filename)
                        elif tool_name == "Read":
                            path = block.input.get("file_path", "")
                            filename = Path(path).name
                            tracker.start("Read", filename)
                print()  # Newline after assistant message

            elif isinstance(message, ResultMessage):
                tracker.complete()
                print(f"\n{'=' * 60}")
                print("Research complete!")
                print(f"Notes saved to: {topic_dir}")
                if message.total_cost_usd:
                    print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"{'=' * 60}\n")
                break


async def follow_up(topic: str) -> None:
    """Continue a research session with follow-up questions."""
    topic_dir = get_topic_dir(topic)

    if not topic_dir.exists():
        print(f"No existing research found for topic: {topic}")
        print("Run initial research first.")
        return

    # Try to detect domain from existing research or use general
    system_prompt = build_system_prompt("general")

    print(f"\n{'=' * 60}")
    print(f"Follow-up Session: {topic}")
    print(f"Research Directory: {topic_dir}")
    print(f"{'=' * 60}\n")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "Read",
            "Write",
            "Glob",
            "Grep",
            "Task",
            "TodoWrite",
        ],
        agents=RESEARCH_AGENTS,
        max_turns=30,
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        # Load existing research context
        context_prompt = f"""You have existing research notes in: {topic_dir}

Read the existing notes to understand what has been researched.
Then wait for the user's follow-up question."""

        await client.query(context_prompt)

        # Process initial context loading
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                print()

        # Interactive follow-up loop
        print("\nReady for follow-up questions. Type 'done' to exit.\n")

        while True:
            try:
                question = input("Follow-up: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                break

            if not question:
                continue
            if question.lower() in ("done", "quit", "exit"):
                print("Session ended.")
                break

            await client.query(question)

            tracker = ToolProgressTracker()
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    tracker.complete()
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="", flush=True)
                        elif isinstance(block, ToolUseBlock):
                            tool_name = block.name
                            if tool_name == "WebSearch":
                                query = block.input.get("query", "")
                                tracker.start("Search", query)
                            elif tool_name == "WebFetch":
                                url = block.input.get("url", "")
                                display_url = url if len(url) < 60 else url[:57] + "..."
                                tracker.start("Fetch", display_url)
                            elif tool_name == "Write":
                                path = block.input.get("file_path", "")
                                tracker.start("Save", Path(path).name)
                    print()
            tracker.complete()


async def research_parallel(topic: str, domain: str | None = None) -> None:
    """Run parallel research with sub-agents."""
    topic_dir = get_topic_dir(topic)

    # Auto-detect domain if not specified
    if domain is None:
        print("[Detecting domain...]")
        domain = await detect_domain(topic)
        print(f"[Domain: {domain}]")

    system_prompt = build_system_prompt(domain)

    print(f"\n{'=' * 60}")
    print(f"Research Topic: {topic}")
    print(f"Mode: Parallel")
    print(f"Domain: {domain}")
    print(f"Output Directory: {topic_dir}")
    print(f"{'=' * 60}\n")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "Read",
            "Write",
            "Glob",
            "Grep",
            "Task",
            "TodoWrite",
        ],
        agents=RESEARCH_AGENTS,
        max_turns=100,  # More turns for coordination
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        decompose_prompt = f"""Research topic: {topic}
Output directory: {topic_dir}

Use PARALLEL research strategy:

1. Analyze topic and identify 2-4 independent research angles
2. Use TodoWrite to create a progress checklist with all angles
3. Use Task tool to spawn "research-thread" sub-agents for each angle IN PARALLEL
   - Each Task call should specify: description, prompt with angle details, subagent_type="research-thread"
   - Launch ALL Task calls in the same message for parallel execution
   - Each sub-agent saves to: {topic_dir}/notes/{{angle-slug}}.md
4. After sub-agents complete, read their outputs
5. Synthesize into {topic_dir}/overview.md
6. Update TodoWrite with all completed

Start by analyzing the topic and identifying research angles."""

        await client.query(decompose_prompt)

        tracker = ToolProgressTracker()
        last_check = time.time()

        async for message in client.receive_messages():
            # Check for slow operations periodically
            now = time.time()
            if now - last_check > 10:
                tracker.check_slow()
                last_check = now

            if isinstance(message, AssistantMessage):
                # Complete any pending tool before showing text
                tracker.complete()

                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.name
                        if tool_name == "WebSearch":
                            query = block.input.get("query", "")
                            tracker.start("Search", query)
                        elif tool_name == "WebFetch":
                            url = block.input.get("url", "")
                            display_url = url if len(url) < 60 else url[:57] + "..."
                            tracker.start("Fetch", display_url)
                        elif tool_name == "Write":
                            path = block.input.get("file_path", "")
                            filename = Path(path).name
                            tracker.start("Save", filename)
                        elif tool_name == "Read":
                            path = block.input.get("file_path", "")
                            filename = Path(path).name
                            tracker.start("Read", filename)
                        elif tool_name == "Task":
                            desc = block.input.get("description", "")
                            tracker.start("Task", desc)
                        elif tool_name == "TodoWrite":
                            tracker.start("TodoWrite", "updating progress")
                print()  # Newline after assistant message

            elif isinstance(message, ResultMessage):
                tracker.complete()
                print(f"\n{'=' * 60}")
                print("Parallel research complete!")
                print(f"Notes saved to: {topic_dir}")
                if message.total_cost_usd:
                    print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"{'=' * 60}\n")
                break


async def synthesize() -> None:
    """Synthesize insights across all research topics."""
    # Check if there are topics to synthesize
    topics = [d for d in TOPICS_DIR.iterdir() if d.is_dir()]
    if not topics:
        print("No research topics found. Run some research first.")
        return

    print(f"\n{'=' * 60}")
    print("Cross-Domain Synthesis")
    print(f"Analyzing {len(topics)} topic(s)")
    print(f"Output Directory: {SYNTHESIS_DIR}")
    print(f"{'=' * 60}\n")

    system_prompt = load_prompt("synthesize.md")

    initial_prompt = f"""Synthesize insights across all research in: {TOPICS_DIR}

Topics to analyze:
{chr(10).join(f'- {t.name}' for t in topics)}

Save your synthesis to: {SYNTHESIS_DIR}
- connections.md: Cross-domain connections
- patterns.md: Recurring themes and principles
- tensions.md: Conflicts and trade-offs
- questions.md: Open questions raised

Start by reading the overview.md from each topic to understand what has been researched."""

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "Read",
            "Write",
            "Glob",
            "Grep",
        ],
        max_turns=50,
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(initial_prompt)

        tracker = ToolProgressTracker()
        last_check = time.time()

        async for message in client.receive_messages():
            now = time.time()
            if now - last_check > 10:
                tracker.check_slow()
                last_check = now

            if isinstance(message, AssistantMessage):
                tracker.complete()
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.name
                        if tool_name == "Write":
                            path = block.input.get("file_path", "")
                            tracker.start("Save", Path(path).name)
                        elif tool_name == "Read":
                            path = block.input.get("file_path", "")
                            tracker.start("Read", Path(path).name)
                print()

            elif isinstance(message, ResultMessage):
                tracker.complete()
                print(f"\n{'=' * 60}")
                print("Synthesis complete!")
                print(f"Results saved to: {SYNTHESIS_DIR}")
                if message.total_cost_usd:
                    print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"{'=' * 60}\n")
                break


async def interactive_session() -> None:
    """Run an interactive research session."""
    print("\n" + "=" * 60)
    print("Project Researcher Agent")
    print("=" * 60)
    print("\nCommands:")
    print("  research <topic>  - Start new research on a topic")
    print("  parallel <topic>  - Research with parallel sub-agents")
    print("  follow <topic>    - Continue with follow-up questions")
    print("  synthesize        - Find connections across all topics")
    print("  quit              - Exit")
    print("\nDomains (auto-detected):")
    print("  tech              - Software, tools, technical topics")
    print("  policy            - Political theory, economics, governance")
    print("  thought-leadership - Finding experts and leading thinkers")
    print("  general           - Everything else")
    print("\nExamples:")
    print("  research Compare MCP servers for Postgres access")
    print("  parallel Compare AI video detection approaches")
    print("  research Universal basic income policy arguments")
    print("  research Who are the leading thinkers on AI alignment")
    print("  follow mcp-servers")
    print("  synthesize")
    print()

    while True:
        try:
            command = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not command:
            continue

        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        elif cmd == "research":
            if not arg:
                print("Usage: research <topic>")
                continue
            await research(arg)
        elif cmd == "follow":
            if not arg:
                print("Usage: follow <topic>")
                continue
            await follow_up(arg)
        elif cmd == "parallel":
            if not arg:
                print("Usage: parallel <topic>")
                continue
            await research_parallel(arg)
        elif cmd == "synthesize":
            await synthesize()
        else:
            # Treat as a research topic if no command prefix
            await research(command)

        print("\nReady for next command.\n")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        # Check for subcommand
        if sys.argv[1] == "follow" and len(sys.argv) > 2:
            topic = " ".join(sys.argv[2:])
            anyio.run(follow_up, topic)
        elif sys.argv[1] == "parallel" and len(sys.argv) > 2:
            topic = " ".join(sys.argv[2:])
            anyio.run(research_parallel, topic)
        elif sys.argv[1] == "synthesize":
            anyio.run(synthesize)
        else:
            # Topic provided as command line argument
            topic = " ".join(sys.argv[1:])
            anyio.run(research, topic)
    else:
        # Interactive mode
        anyio.run(interactive_session)


if __name__ == "__main__":
    main()
