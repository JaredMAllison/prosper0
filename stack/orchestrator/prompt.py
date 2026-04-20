from pathlib import Path

ARIEL_PERSONA = """
You are Ariel, a work assistant running on Prosper0.
You help with task management, project tracking, and knowledge work
within the scope defined by your configuration.

Current mode: {mode}
Session: {session_id}
""".strip()


def build_system_prompt(
    mode: str,
    session_id: str,
    memory_dir: Path | None = None,
    skills_dir: Path | None = None,
) -> str:
    parts = [ARIEL_PERSONA.format(mode=mode, session_id=session_id)]

    if memory_dir and memory_dir.exists():
        parts += _load_memories(memory_dir, mode)

    if skills_dir and skills_dir.exists():
        parts += _load_skill(skills_dir, mode)

    return "\n\n".join(parts)


def _load_memories(memory_dir: Path, mode: str) -> list[str]:
    """Load all memory files from memory_dir. Mode filtering is future work."""
    memories = []
    for path in sorted(memory_dir.glob("*.md")):
        text = path.read_text().strip()
        if text:
            memories.append(text)
    return memories


def _load_skill(skills_dir: Path, mode: str) -> list[str]:
    """Load the skill template matching the current mode, if one exists."""
    skill_file = skills_dir / f"{mode}.md"
    if skill_file.exists():
        text = skill_file.read_text().strip()
        if text:
            return [text]
    return []
