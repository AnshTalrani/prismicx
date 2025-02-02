import unittest
from validation.validation_module import ValidationModule
from models.user_insight import UserInsight
from models.practicality import Practicality
from models.secret_sauce import SecretSauce
from models.factor import Factor
from models.user_insight_extension import UserInsightExtension

class TestValidationModule(unittest.TestCase):
    """Unit tests for ValidationModule."""

    def setUp(self):
        self.validator = ValidationModule()

    def test_validate_insight_success(self):
        """Test validating a correct UserInsight."""
        insight = UserInsight("user_1")
        insight.topics = []
        self.assertFalse(self.validator.validateInsight(insight))  # Should fail due to no topics

        # Adding topics
        from models.topic import Topic
        insight.topics.append(Topic("topic_1", "Topic Name"))
        self.assertTrue(self.validator.validateInsight(insight))

    def test_validate_practicality_success(self):
        """Test validating a correct Practicality."""
        practicality = Practicality("practicality_1", "user_1")
        practicality.secretSauces = [SecretSauce("sauce_1", "Delicious", "layer_1")]
        practicality.factors = [Factor("factor_1", "Factor Name", "Description")]
        practicality.batchIDs = ["batch_1"]
        self.assertTrue(self.validator.validatePracticality(practicality))

    def test_validate_extension_failure(self):
        """Test validating an incorrect UserInsightExtension."""
        extension = UserInsightExtension("", "template_1", {}, "batch_1")
        self.assertFalse(self.validator.validateExtension(extension))

if __name__ == '__main__':
    unittest.main() 