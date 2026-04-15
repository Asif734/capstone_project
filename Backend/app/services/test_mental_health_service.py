import os
import tempfile
import unittest

from app.services.mental_health_service import MentalHealthService
from app.services.memory_service import MemoryService


class MentalHealthServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.memory_service = MemoryService(file_path=self.temp_file.name)
        self.service = MentalHealthService(memory_service=self.memory_service)

    def tearDown(self):
        try:
            os.unlink(self.temp_file.name)
        except OSError:
            pass

    def test_ml_model_loaded(self):
        self.assertTrue(self.service.use_ml, "LightGBM should be loaded as the primary detector")
        self.assertEqual(type(self.service.model).__name__, "LGBMClassifier")

    def test_analyze_history_returns_high_risk_for_suicidal_text(self):
        interactions = [
            {"question": "I feel depressed and suicidal and I don't want to live", "answer": ""}
        ]
        analysis = self.service.analyze_history(interactions)

        self.assertIn("risk_level", analysis)
        self.assertIn(analysis["risk_level"], ["high", "moderate", "normal"])
        self.assertGreaterEqual(analysis["confidence"], 0.0)
        self.assertGreater(analysis["score"], 0)
        self.assertTrue(
            self.service.should_alert(analysis),
            f"Expected alert for suicidal text, got analysis={analysis}"
        )


if __name__ == "__main__":
    unittest.main()
