"""
Entry point for the Prosper0 orchestrator.
Reads config from environment, builds the stack, runs the agent loop.
"""
import os
import sys
import uuid
from pathlib import Path

import httpx

from .backend import ModelBackend
from .ollama import OllamaBackend
from .prompt import build_system_prompt
from .loop import run, MaxIterationsError
from .config import load_tools_config
from ..mcp.registry import make_tool_executor
from ..mcp.definitions import TOOL_DEFINITIONS


def _build_gate(config_path: Path, log_dir: Path, session_id: str):
    """Wire up the enforcement chain. Imports transparency package at runtime."""
    try:
        import yaml
        from transparency.enforcement.config import ToolsConfig
        from transparency.enforcement.audit_logger import AuditLogger
        from transparency.enforcement.chain import EnforcementChain

        raw = load_tools_config(config_path)
        tools_config = ToolsConfig.from_dict(raw)
        audit = AuditLogger(log_dir)
        return EnforcementChain(
            config=tools_config,
            audit=audit,
            smtp_config={},
            session_id=session_id,
            log_dir=log_dir,
        )
    except ImportError:
        print("[warn] transparency package not found — enforcement disabled", file=sys.stderr)
        return _NoOpGate()


class _NoOpGate:
    def call(self, tool_name, path, executor, is_transfer=False):
        return executor()


def main():
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    vault_path = Path(os.environ.get("VAULT_PATH", "./vault"))
    config_path = Path(os.environ.get("TOOLS_CONFIG_PATH", "./tools.config.yaml"))
    log_dir = Path(os.environ.get("AUDIT_LOG_PATH", "./logs"))
    mode = os.environ.get("PROSPER0_MODE", "available")
    timeout = float(os.environ.get("OLLAMA_TIMEOUT", "600"))
    session_id = str(uuid.uuid4())[:8]
    memory_dir = Path(os.environ.get("MEMORY_PATH", str(vault_path / "memory")))
    skills_dir = Path(os.environ.get("SKILLS_PATH", str(vault_path / "skills")))

    backend = OllamaBackend(host=ollama_host, model=model, timeout=timeout)
    gate = _build_gate(config_path, log_dir, session_id)
    tool_executor = make_tool_executor(vault_root=vault_path)
    system_prompt = build_system_prompt(
        mode=mode,
        session_id=session_id,
        memory_dir=memory_dir,
        skills_dir=skills_dir,
    )

    print(f"Ariel von Prosper0 — mode: {mode} | session: {session_id}")
    print("Type your message. Ctrl+C to exit.\n")

    messages = []
    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            response = run(backend, gate, tool_executor, messages, TOOL_DEFINITIONS, system_prompt)
            messages.append({"role": "assistant", "content": response})
            print(f"\nAriel: {response}\n")
        except MaxIterationsError as e:
            print(f"[error] {e}", file=sys.stderr)
        except httpx.ReadTimeout:
            messages.pop()  # remove the unanswered user message
            print("[timeout] Inference timed out — the model is thinking too slowly on CPU. Try a shorter message or wait for GPU support.", file=sys.stderr)


if __name__ == "__main__":
    main()
