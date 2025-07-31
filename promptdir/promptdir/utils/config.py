"""Configuration utilities."""

import json
from pathlib import Path

# Configuration file location
CONFIG_FILE = Path.home() / ".config" / "promptdir" / "config.json"

def load_config() -> dict:
    """Load configuration from config file"""
    if not CONFIG_FILE.exists():
        # Create default config
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "prompt_repo": ""
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config: dict):
    """Save configuration to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
