"""Configuration loader utility."""
import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_config() -> Dict[str, Any]:
    """Get configuration with default path."""
    return load_config()

