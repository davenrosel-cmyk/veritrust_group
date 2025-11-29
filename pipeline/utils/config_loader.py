import yaml
from pathlib import Path


def load_config(path: str = "config.yaml") -> dict:
    """
    Load YAML configuration (root-level) and return as dict.
    Environment variables can override keys (optional future extension).
    """
    cfg_path = Path(path)

    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
