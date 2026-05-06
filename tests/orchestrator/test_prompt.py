import pytest
from pathlib import Path

from stack.orchestrator.prompt import build_system_prompt


def test_persona_contains_mode_and_session(tmp_path):
    result = build_system_prompt(mode="available", session_id="2026-04-20-1")
    assert "available" in result
    assert "2026-04-20-1" in result


def test_persona_contains_ariel_name(tmp_path):
    result = build_system_prompt(mode="deep-work", session_id="test")
    assert "Ariel" in result


def test_loads_memory_files(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "user_role.md").write_text("Jared is a software engineer.")

    result = build_system_prompt(mode="available", session_id="test", memory_dir=memory_dir)
    assert "Jared is a software engineer." in result


def test_skips_missing_memory_dir(tmp_path):
    result = build_system_prompt(
        mode="available", session_id="test", memory_dir=tmp_path / "nonexistent"
    )
    assert "Ariel" in result  # persona still present; no crash


def test_loads_skill_for_mode(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "available.md").write_text("In available mode: surface tasks proactively.")

    result = build_system_prompt(mode="available", session_id="test", skills_dir=skills_dir)
    assert "surface tasks proactively" in result


def test_no_skill_loaded_when_mode_has_no_file(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    result = build_system_prompt(mode="deep-work", session_id="test", skills_dir=skills_dir)
    assert "Ariel" in result  # no crash, persona intact
