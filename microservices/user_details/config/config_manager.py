import json
import os

class ConfigManager:
    """Manages template configurations."""

    def __init__(self):
        """Initialize ConfigManager with templates from environment or files."""
        self.templates = self.load_templates()

    def load_templates(self):
        """Load templates from a secure source."""
        templates_path = os.getenv('TEMPLATES_PATH', 'config/templates.json')
        with open(templates_path, 'r') as file:
            return json.load(file)

    def getTemplate(self, templateID: str):
        """Retrieve a template by its ID."""
        return self.templates.get(templateID)

    def addTemplate(self, template: dict):
        """Add a new template."""
        self.templates[template['templateID']] = template
        self.save_templates()

    def removeTemplate(self, templateID: str):
        """Remove a template by its ID."""
        if templateID in self.templates:
            del self.templates[templateID]
            self.save_templates()

    def updateTemplate(self, templateID: str, template: dict):
        """Update an existing template."""
        self.templates[templateID] = template
        self.save_templates()

    def save_templates(self):
        """Persist templates to a secure storage."""
        templates_path = os.getenv('TEMPLATES_PATH', 'config/templates.json')
        with open(templates_path, 'w') as file:
            json.dump(self.templates, file, indent=4) 