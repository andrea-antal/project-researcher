#!/usr/bin/env python3
"""
Project Researcher Agent

An interactive research agent that:
1. Takes a research topic
2. Asks clarifying questions to understand scope
3. Searches the web for relevant sources
4. Extracts and synthesizes information
5. Builds a local knowledge base
6. Answers follow-up questions using accumulated context
"""

import re
import sys
from pathlib import Path

import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from config import PROMPTS_DIR, TOPICS_DIR


def load_system_prompt() -> str:
    """Load the researcher system prompt."""
    prompt_file = PROMPTS_DIR / "researcher.md"
    return prompt_file.read_text()


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


async def research(topic: str) -> None:
    """Run the research agent on a topic."""
    topic_dir = get_topic_dir(topic)
    system_prompt = load_system_prompt()

    # Build the initial prompt with context about where to save
    initial_prompt = f"""Research topic: {topic}

Save your findings to: {topic_dir}
- overview.md: Main summary and recommendations
- sources.md: List of sources with key excerpts
- notes/: Detailed notes on subtopics

Start by asking clarifying questions to understand what aspects matter most."""

    print(f"\n{'=' * 60}")
    print(f"Research Topic: {topic}")
    print(f"Output Directory: {topic_dir}")
    print(f"{'=' * 60}\n")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "AskUserQuestion",
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

        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.name
                        if tool_name == "WebSearch":
                            query = block.input.get("query", "")
                            print(f"\n[Searching: {query}...]\n")
                        elif tool_name == "WebFetch":
                            url = block.input.get("url", "")
                            print(f"\n[Fetching: {url}...]\n")
                        elif tool_name == "Write":
                            path = block.input.get("file_path", "")
                            print(f"\n[Saving: {path}...]\n")
                        elif tool_name == "AskUserQuestion":
                            print("\n")  # Extra line before questions
                print()  # Newline after assistant message

            elif isinstance(message, ResultMessage):
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
    system_prompt = load_system_prompt()

    if not topic_dir.exists():
        print(f"No existing research found for topic: {topic}")
        print("Run initial research first.")
        return

    print(f"\n{'=' * 60}")
    print(f"Follow-up Session: {topic}")
    print(f"Research Directory: {topic_dir}")
    print(f"{'=' * 60}\n")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "AskUserQuestion",
            "Read",
            "Write",
            "Glob",
            "Grep",
        ],
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

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="", flush=True)
                        elif isinstance(block, ToolUseBlock):
                            tool_name = block.name
                            if tool_name == "WebSearch":
                                query = block.input.get("query", "")
                                print(f"\n[Searching: {query}...]\n")
                            elif tool_name == "WebFetch":
                                url = block.input.get("url", "")
                                print(f"\n[Fetching: {url}...]\n")
                    print()


async def interactive_session() -> None:
    """Run an interactive research session."""
    print("\n" + "=" * 60)
    print("Project Researcher Agent")
    print("=" * 60)
    print("\nCommands:")
    print("  research <topic>  - Start new research on a topic")
    print("  follow <topic>    - Continue with follow-up questions")
    print("  quit              - Exit")
    print("\nExamples:")
    print("  research Compare MCP servers for Postgres access")
    print("  research Best practices for React state management")
    print("  follow mcp-servers")
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
        else:
            # Topic provided as command line argument
            topic = " ".join(sys.argv[1:])
            anyio.run(research, topic)
    else:
        # Interactive mode
        anyio.run(interactive_session)


if __name__ == "__main__":
    main()
