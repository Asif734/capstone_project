import unittest

from app.utils.graph import get_greeting_response, response_language_instruction, route_question


class RouteQuestionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
