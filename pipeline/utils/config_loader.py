"""
Load and validate Tier‑0 configuration.

Implements:
    - atomic, deterministic config loading
    - strict schema validation using Pydantic
    - environment variable overrides (optional)
    - absolute imports (Feedback v3)
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ValidationError


class PipelineConfig(BaseModel):
    """
    Strongly‑typed Tier‑0 configuration model.

    All fields are required because the pipeline must be deterministic.
    """

    input_file: str = Field(..., description="Local SRA input file path")
    raw_output_dir: str = Field(..., description="Directory for raw audit dumps")
    normalized_output_dir: str = Field(..., description="Directory for normalized intermediates")

    jsonld_firms: str = Field(..., description="Output path for firms.jsonld")
    jsonld_dataset: str = Field(..., description="Output path for dataset.jsonld")
    jsonld_manifest: str = Field(..., description="Output path for manifest.jsonld")
    
    public_files_base: str | None = None
    public_id_base: str | None = None

    head_office_code: str = "HEAD OFFICE"

    fetch_url: str = Field(..., description="URL to fetch SRA dataset from")
    subscription_key: str = Field(..., description="Subscription key for SRA API")


def _apply_env_overrides(cfg: dict) -> dict:
    """
    Apply environment variable overrides if they exist.

    Example:
        export VT_INPUT_FILE="data/custom.json"

    Supported env variables:
        VT_INPUT_FILE
        VT_RAW_OUTPUT_DIR
        VT_NORMALIZED_OUTPUT_DIR
        VT_JSONLD_FIRMS
        VT_JSONLD_DATASET
        VT_JSONLD_MANIFEST
    """

    mapping = {
        "VT_INPUT_FILE": "input_file",
        "VT_RAW_OUTPUT_DIR": "raw_output_dir",
        "VT_NORMALIZED_OUTPUT_DIR": "normalized_output_dir",
        "VT_JSONLD_FIRMS": "jsonld_firms",
        "VT_JSONLD_DATASET": "jsonld_dataset",
        "VT_JSONLD_MANIFEST": "jsonld_manifest",
    }

    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            cfg[cfg_key] = os.environ[env_key]

    return cfg


def load_config(path: str = "config.yaml") -> PipelineConfig:
    """
    Load YAML configuration, apply env overrides, validate via Pydantic,
    and return a strongly‑typed PipelineConfig object.

    Args:
        path: Path to config.yaml

    Returns:
        PipelineConfig

    Raises:
        FileNotFoundError: If config.yaml does not exist.
        ValidationError: If configuration keys or values are invalid.
        OSError: If reading config fails.
    """
    cfg_path = Path(path)

    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg_dict = yaml.safe_load(f)
    except OSError as e:
        raise OSError(f"Failed to read configuration file: {e}")

    if not isinstance(cfg_dict, dict):
        raise ValueError("Invalid configuration file: expected YAML dictionary at root")

    cfg_dict = _apply_env_overrides(cfg_dict)

    try:
        return PipelineConfig(**cfg_dict)
    except ValidationError as e:
        # Feedback v3: do NOT catch generic exception; catch specific Pydantic error only
        raise ValidationError(f"Invalid configuration: {e}") from e
