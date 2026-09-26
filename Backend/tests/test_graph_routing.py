import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from app.utils.graph import (
    detect_greeting,
    build_retrieval_question,
    get_greeting_response,
    mental_support_agent,
    response_language_instruction,
    route_question,
)


class RouteQuestionTests(unittest.TestCase):
    def test_greeting_must_be_the_whole_message(self):
        self.assertTrue(detect_greeting("hi buddy"))
        self.assertFalse(detect_greeting("hi, what courses are available?"))
        self.assertFalse(detect_greeting("I think I should reconsider"))

    def test_greeting_plus_question_routes_to_rag(self):
        self.assertEqual(route_question("Hi, what courses are available?"), "rag")

    def test_specialization_query_is_expanded_for_program_retrieval(self):
        expanded = build_retrieval_question("Are there specialization courses?", [])
        self.assertIn("degree program", expanded)
        self.assertIn("MBA specialization", expanded)

    def test_do_you_know_me_routes_to_student_when_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=True), "student")

    def test_do_you_know_me_requires_login_when_not_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=False), "auth_required")

    def test_casual_how_are_you_gets_natural_response(self):
        self.assertEqual(
            get_greeting_response("how are you buddy?"),
            "I'm doing well, buddy. How are you doing?",
        )

    def test_result_worry_routes_to_mental_support_not_login_block(self):
        self.assertEqual(
            route_question("i can't stay positive, i think my result is going to be worse than before"),
            "mental_support",
        )

    def test_not_feeling_good_routes_to_mental_support(self):
        self.assertEqual(route_question("not feeling good"), "mental_support")

    def test_dynamic_assessment_can_route_ambiguous_distress(self):
        assessment = {"response_mode": "clarify"}
        self.assertEqual(
            route_question("I think I am not feeling well", mental_health_assessment=assessment),
            "mental_support",
        )

    def test_public_course_question_does_not_require_authentication(self):
        self.assertEqual(route_question("Is there any specialization course?"), "rag")

    def test_personal_course_question_requires_authentication(self):
        self.assertEqual(route_question("What are my courses?"), "auth_required")

    def test_course_decision_is_not_mistaken_for_private_student_data(self):
        self.assertEqual(
            route_question("I think I should not join the master's course"),
            "chat",
        )

    def test_academics_not_going_well_routes_to_mental_support(self):
        self.assertEqual(route_question("my academics are not going well at all"), "mental_support")

    def test_crisis_language_routes_to_safety_support(self):
        self.assertEqual(route_question("i want to die"), "mental_support")

    def test_no_reason_to_live_routes_to_safety_support(self):
        self.assertEqual(route_question("I see no reason to live anymore"), "mental_support")

    def test_do_not_want_to_live_routes_to_safety_support(self):
        self.assertEqual(route_question("I don't want to live"), "mental_support")

    def test_short_why_after_support_stays_in_mental_support_context(self):
        history = [
            {
                "question": "i can't stay positive, i think my result is going to be worse than before",
                "answer": "I'm really sorry you're feeling this way. You do not have to handle it alone.",
            }
        ]

        self.assertEqual(route_question("why?", conversation_history=history), "mental_support")

    def test_english_message_requires_english_response(self):
        self.assertEqual(
            response_language_instruction("hey buddy, feeling stressed"),
            "Reply in English only. Do not use Bengali script.",
        )

    def test_banglish_message_requires_banglish_response(self):
        self.assertEqual(
            response_language_instruction("tmi kemon acho, AMi valo achi"),
            "Reply in Banglish, using romanized Bangla words and English letters only. Do not use Bengali script.",
        )

    def test_bangla_message_requires_bangla_response(self):
        self.assertEqual(
            response_language_instruction("তুমি কেমন আছো"),
            "Reply in Bangla using Bengali script only.",
        )

    def test_mixed_banglish_message_requires_consistent_banglish_response(self):
        self.assertEqual(
            response_language_instruction("Amar kemon acho tumi? Tumi BUP-এর assistant."),
            "Reply in Banglish, using romanized Bangla words and English letters only. Do not use Bengali script.",
        )

    def test_banglish_greeting_returns_banglish_without_llm(self):
        self.assertEqual(
            get_greeting_response("kemon acho tumi?"),
            "Ami bhalo achi, dhonnobad! Ami BUP-er secure multilingual assistant. Apni ki jante chan?",
        )

    def test_bangla_greeting_returns_bengali_script(self):
        self.assertEqual(
            get_greeting_response("তুমি কেমন আছো?"),
            "আমি ভালো আছি, ধন্যবাদ! আপনি কী জানতে চান?",
        )

    def test_common_banglish_typo_greeting_is_handled_without_llm(self):
        self.assertTrue(detect_greeting("kemn acho?"))
        self.assertEqual(
            get_greeting_response("kemn acho?"),
            "Ami bhalo achi, dhonnobad! Ami BUP-er secure multilingual assistant. Apni ki jante chan?",
        )

    def test_bengali_polite_greeting_is_handled_without_llm(self):
        self.assertTrue(detect_greeting("আপনি কেমন আছেন?"))
        self.assertEqual(
            get_greeting_response("আপনি কেমন আছেন?"),
            "আমি ভালো আছি, ধন্যবাদ! আপনি কী জানতে চান?",
        )

    def test_support_has_safe_fallback_when_llm_is_unavailable(self):
        def fail(_):
            raise ConnectionError("Ollama unavailable")

        state = {
            "question": "I am not feeling well",
            "conversation_history": [],
            "mental_health_assessment": {"response_mode": "clarify"},
        }
        with self.assertLogs("app.utils.graph", level="ERROR"):
            with patch("app.utils.graph.llm", RunnableLambda(fail)):
                result = mental_support_agent(state)

        self.assertIn("physical illness", result["answer"])
        self.assertNotIn("emergency", result["answer"].lower())

    def test_bangla_crisis_response_uses_bangla(self):
        result = mental_support_agent({
            "question": "আমি আত্মহত্যা করতে চাই",
            "conversation_history": [],
            "mental_health_assessment": {"response_mode": "crisis"},
        })
        self.assertIn("আপনাকে একা", result["answer"])


if __name__ == "__main__":
    unittest.main()
