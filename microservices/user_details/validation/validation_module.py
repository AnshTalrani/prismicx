from models.user_insight import UserInsight
from models.practicality import Practicality
from models.user_insight_extension import UserInsightExtension

class ValidationModule:
    """Module for validating UserInsight, Practicality, and UserInsightExtension objects."""

    def validateInsight(self, insight: UserInsight) -> bool:
        """Validate a UserInsight object."""
        if not insight.userID:
            return False
        if not insight.topics:
            return False
        # Add more validation rules as needed
        return True

    def validatePracticality(self, practicality: Practicality) -> bool:
        """Validate a Practicality object."""
        if not practicality.practicalityID:
            return False
        if not practicality.userID:
            return False
        # Validate secretSauces and factors
        for sauce in practicality.secretSauces:
            if not sauce.sauceID or not sauce.description:
                return False
        for factor in practicality.factors:
            if not factor.factorID or not factor.name:
                return False
        return True

    def validateExtension(self, extension: UserInsightExtension) -> bool:
        """Validate a UserInsightExtension object."""
        if not extension.userID or not extension.templateID:
            return False
        if not isinstance(extension.metrics, dict):
            return False
        # Add more validation rules as needed
        return True

    def validate_template(self, template_id: str) -> bool:
        """Validate template ID structure"""
        parts = template_id.split('_')
        if len(parts) < 2:
            return False
        if parts[0] not in ["pre", "pro", "post"]:
            return False
        return True 