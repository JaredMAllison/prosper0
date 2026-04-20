import yaml
from pathlib import Path


def load_tools_config(path: Path) -> dict:
    """Load tools.config.yaml and return raw dict. Validation is enforcement layer's job."""
    with open(path) as f:
        return yaml.safe_load(f)
