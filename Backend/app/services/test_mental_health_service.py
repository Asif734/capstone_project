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
        self.assertTrue(self.service.use_ml, "Mental health ML model should be loaded")
        self.assertIn(type(self.service.model).__name__, ["SGDClassifier", "LGBMClassifier"])
        self.assertTrue(self.service.is_multilingual, "Multilingual model bundle should be active")
        self.assertGreater(len(self.service.classes), 0)

    def test_multilingual_bangla_distress_detection(self):
        interactions = [
            {"question": "আমি সবকিছু নিয়ে খুব ক্লান্ত, মনে হচ্ছে বেঁচে থাকার আর কোনো অর্থ নেই", "answer": ""}
        ]
        analysis = self.service.analyze_history(interactions)
        self.assertIn(analysis["risk_level"], ["high", "moderate"])
        self.assertTrue(self.service.should_alert(analysis))

    def test_multilingual_banglish_distress_detection(self):
        interactions = [
            {"question": "amar khub depression lagche, jibon e sob kichu sesh mone hocche", "answer": ""}
        ]
        analysis = self.service.analyze_history(interactions)
        self.assertIn(analysis["risk_level"], ["high", "moderate"])
        self.assertTrue(self.service.should_alert(analysis))

    def test_multilingual_normal_queries_stay_safe(self):
        queries = [
            "Hey could you tell me where the library is located?",
            "ajke class er timing ki change hoise dosto?",
            "আগামীকাল আমাদের প্রেজেন্টেশনের সময় কয়টায়?",
        ]
        for q in queries:
            analysis = self.service.analyze_history([{"question": q, "answer": ""}])
            self.assertEqual(analysis["risk_level"], "normal", f"Query '{q}' should be classified as normal")
            self.assertFalse(self.service.should_alert(analysis))

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

    def test_rule_scoring_flags_do_not_want_to_live_as_high_risk(self):
        result = self.service.score_message("I don't want to live")

        self.assertGreaterEqual(result["score"], 10)
        self.assertTrue(result["high_hits"])

    def test_ambiguous_unwell_message_asks_for_clarification(self):
        assessment = self.service.assess_message("I think I am not feeling well")

        self.assertEqual(assessment["category"], "ambiguous_distress")
        self.assertEqual(assessment["response_mode"], "clarify")
        self.assertFalse(assessment["current_high_hits"])

    def test_academic_uncertainty_is_not_treated_as_a_crisis(self):
        assessment = self.service.assess_message(
            "I think I should not join the master's course"
        )

        self.assertNotEqual(assessment["response_mode"], "crisis")
        self.assertFalse(assessment["current_high_hits"])

    def test_bangla_crisis_language_is_detected(self):
        assessment = self.service.assess_message("আমি বাঁচতে চাই না")
        self.assertEqual(assessment["response_mode"], "crisis")

    def test_banglish_ambiguous_distress_is_clarified(self):
        assessment = self.service.assess_message("amar bhalo lagche na")
        self.assertEqual(assessment["response_mode"], "clarify")

    def test_fallback_alert_summary_is_one_line_and_informative(self):
        interactions = [
            {"question": "My academics are not going well and I feel stressed", "answer": ""}
        ]
        analysis = {
            "risk_level": "moderate",
            "recent_messages": [interactions[0]["question"]],
        }

        summary = self.service.fallback_alert_summary(interactions, analysis)

        self.assertIn("moderate", summary)
        self.assertIn("academics", summary)
        self.assertNotIn("\n", summary)


if __name__ == "__main__":
    unittest.main()
