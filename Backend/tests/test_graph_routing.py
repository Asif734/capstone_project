import unittest

from app.utils.graph import route_question


class RouteQuestionTests(unittest.TestCase):
    def test_do_you_know_me_routes_to_student_when_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=True), "student")

    def test_do_you_know_me_requires_login_when_not_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=False), "auth_required")


if __name__ == "__main__":
    unittest.main()
