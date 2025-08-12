import json
from pathlib import Path
from typing import Dict, Any

TEMPLATE_DIR = Path(__file__).parent.parent / "config"

def load_campaign_template(template_name: str) -> Dict[str, Any]:
    """
    Load a campaign template JSON by name from the config directory.
    Args:
        template_name: Filename of the template (e.g., 'campaign_template_example.json')
    Returns:
        Parsed template as a dictionary
    Raises:
        FileNotFoundError if the template does not exist
        json.JSONDecodeError if the template is invalid
    """
    path = TEMPLATE_DIR / template_name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
