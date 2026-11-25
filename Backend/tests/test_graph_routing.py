import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from app.utils.graph import (
    detect_greeting,
    assistant_identity_response,
    build_retrieval_question,
    build_contextual_question,
    clean_llm_output,
    get_greeting_response,
    is_contextual_follow_up,
    mental_support_agent,
    format_identity_answer,
    rag_prompt,
    response_language_code,
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

    def test_masters_program_correction_is_routed_and_expanded(self):
        question = "bup has masters course"
        self.assertEqual(route_question(question), "rag")
        self.assertEqual(
            build_retrieval_question(question, []),
            "What master's programs does BUP offer?",
        )

    def test_short_follow_up_keeps_previous_question_for_retrieval(self):
        expanded = build_retrieval_question(
            "কম্পিউটার বিজ্ঞান",
            [{"question": "মাস্টার্স পর্যায়ের কোর্সগুলো কী কী?", "answer": "..."}],
        )
        self.assertIn("মাস্টার্স পর্যায়ের কোর্সগুলো কী কী?", expanded)
        self.assertIn("কম্পিউটার বিজ্ঞান", expanded)

    def test_do_you_know_me_routes_to_student_when_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=True), "student")

    def test_do_you_know_me_requires_login_when_not_authenticated(self):
        self.assertEqual(route_question("do you know me?", is_authenticated=False), "auth_required")

    def test_banglish_name_question_routes_to_student_when_authenticated(self):
        self.assertEqual(route_question("amar nam ki?", is_authenticated=True), "student")

    def test_banglish_name_question_requires_login_when_not_authenticated(self):
        self.assertEqual(route_question("amar naam ki?", is_authenticated=False), "auth_required")

    def test_bangla_identity_questions_route_to_student(self):
        for question in ("আমার নাম কী?", "আপনি কি আমাকে চেনেন?"):
            self.assertEqual(route_question(question, is_authenticated=True), "student")

    def test_assistant_identity_questions_route_to_chat(self):
        self.assertEqual(route_question("tumi ke?"), "chat")
        self.assertEqual(route_question("tmar kaj ki?"), "chat")

    def test_identity_answers_use_record_name_and_question_language(self):
        self.assertEqual(format_identity_answer("আমার নাম কী?", "Amar"), "আপনার নাম Amar।")
        self.assertEqual(format_identity_answer("amar nam ki?", "Amar"), "Your name is Amar.")
        self.assertEqual(format_identity_answer("who am i?", "Amar"), "Your name is Amar.")

    def test_assistant_identity_answers_are_english_for_banglish(self):
        self.assertEqual(
            assistant_identity_response("tumi ke?"),
            "I'm the BUP Student Assistant. I can help with student support and BUP-related questions.",
        )
        self.assertEqual(
            assistant_identity_response("tmar kaj ki?"),
            "I help with student support, academic information, and other BUP-related questions.",
        )

    def test_bangla_know_me_answer_is_record_based(self):
        self.assertEqual(
            format_identity_answer("আপনি কি আমাকে চেনেন?", "Amar"),
            "ব্যক্তিগতভাবে নয়, তবে আপনার শিক্ষার্থী রেকর্ডে আপনার নাম Amar দেওয়া আছে।",
        )

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
            "rag_fallback",
        )

    def test_unclassified_bangla_question_tries_retrieval_before_chat(self):
        self.assertEqual(route_question("ভর্তি প্রক্রিয়াটি কী?"), "rag_fallback")

    def test_academics_not_going_well_routes_to_mental_support(self):
        self.assertEqual(route_question("my academics are not going well at all"), "mental_support")

    def test_semester_drop_inquiry_routes_to_mental_support(self):
        self.assertEqual(
            route_question("amar ki semester drop dewa ucit.. i think i should"),
            "mental_support",
        )

    def test_bad_result_and_quit_study_routes_to_mental_support(self):
        self.assertEqual(
            route_question("amar last semester er result onek kharap hoise.. ami mone hoi chere dibo"),
            "mental_support",
        )
        self.assertEqual(
            route_question("no, i think amar poralekha chere dewa ucit. ar valo lagteche na"),
            "mental_support",
        )

    def test_support_follow_up_on_semester_drop_stays_in_mental_support(self):
        history = [
            {
                "question": "no, i think amar poralekha chere dewa ucit. ar valo lagteche na",
                "answer": "It sounds like you're feeling a bit stuck and unsure about your path forward. Can I help you explore some options for next semester or connect you with resources that might support you in your academic journey?",
            }
        ]
        self.assertEqual(
            route_question("amar ki semester drop dewa ucit.. i think i should", conversation_history=history),
            "mental_support",
        )

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
            "Reply only in fluent English. Do not use Banglish, romanized Bengali, Hindi, or any other language. Do not mirror the user's language.",
        )

    def test_banglish_message_requires_english_response(self):
        self.assertEqual(
            response_language_instruction("tmi kemon acho, AMi valo achi"),
            "Reply only in fluent English. Do not use Banglish, romanized Bengali, Hindi, or any other language. Do not mirror the user's language.",
        )

    def test_bangla_message_requires_bangla_response(self):
        self.assertEqual(
            response_language_instruction("তুমি কেমন আছো"),
            "Reply in Bangla using Bengali script only.",
        )

    def test_response_language_code_groups_banglish_with_english(self):
        self.assertEqual(response_language_code("tumi kemon acho"), "en")
        self.assertEqual(response_language_code("তুমি কেমন আছো"), "bn")

    def test_mixed_banglish_message_requires_english_response(self):
        self.assertEqual(
            response_language_instruction("Amar kemon acho tumi? Tumi BUP-এর assistant."),
            "Reply only in fluent English. Do not use Banglish, romanized Bengali, Hindi, or any other language. Do not mirror the user's language.",
        )

    def test_banglish_greeting_returns_english_without_llm(self):
        self.assertEqual(
            get_greeting_response("kemon acho tumi?"),
            "I'm doing well, thanks! What can I help you with?",
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
            "I'm doing well, thanks! What can I help you with?",
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

    def test_banglish_support_fallback_uses_english(self):
        def fail(_):
            raise ConnectionError("Ollama unavailable")

        state = {
            "question": "ami not feeling well",
            "conversation_history": [],
            "mental_health_assessment": {"response_mode": "clarify"},
        }
        with self.assertLogs("app.utils.graph", level="ERROR"):
            with patch("app.utils.graph.llm", RunnableLambda(fail)):
                result = mental_support_agent(state)

        self.assertIn("physical illness", result["answer"])

    def test_bangla_crisis_response_uses_bangla(self):
        result = mental_support_agent({
            "question": "আমি আত্মহত্যা করতে চাই",
            "conversation_history": [],
            "mental_health_assessment": {"response_mode": "crisis"},
        })
        self.assertIn("আপনাকে একা", result["answer"])

    def test_banglish_crisis_response_uses_english(self):
        result = mental_support_agent({
            "question": "ami bachte chai na",
            "conversation_history": [],
            "mental_health_assessment": {"response_mode": "crisis"},
        })
        self.assertIn("If you might hurt yourself", result["answer"])

    def test_conversational_reactions_route_to_chat(self):
        reactions = [
            "oho, you are too fast",
            "thanks buddy",
            "wow awesome",
            "okay got it",
            "দারুণ!",
            "ধন্যবাদ",
        ]
        for query in reactions:
            self.assertEqual(route_question(query), "chat", f"Failed for query: {query}")

    def test_masters_course_inquiry_expands_to_programs(self):
        expanded = build_retrieval_question(
            "i want to masters, what are the courses available here?",
            [],
        )
        self.assertEqual(expanded, "What master's programs does BUP offer?")

    def test_language_continuity_for_short_replies(self):
        bengali_history = [
            {
                "question": "আমি সবকিছু নিয়ে খুব ক্লান্ত, মনে হচ্ছে বেঁচে থাকার আর কোনো অর্থ নেই",
                "answer": "আপনার এমন লাগছে শুনে আমি খুব দুঃখিত—আপনাকে একা এটি সামলাতে হবে না। আপনি কি এখন তাৎক্ষণিক ঝুঁকিতে আছেন?",
            }
        ]
        self.assertEqual(response_language_code("ha", bengali_history), "bn")
        self.assertIn("Bangla", response_language_instruction("ha", bengali_history))
        self.assertEqual(response_language_code("ji", bengali_history), "bn")

    def test_affirmative_crisis_follow_up_stays_in_mental_support_and_bangla(self):
        bengali_crisis_history = [
            {
                "question": "আমি আত্মহত্যা করতে চাই",
                "answer": "আপনার এমন লাগছে শুনে আমি খুব দুঃখিত—আপনাকে একা এটি সামলাতে হবে না। আপনি কি এখন তাৎক্ষণিক ঝুঁকিতে আছেন?",
            }
        ]
        self.assertEqual(
            route_question("ha", conversation_history=bengali_crisis_history),
            "mental_support",
        )
        result = mental_support_agent({
            "question": "ha",
            "conversation_history": bengali_crisis_history,
            "mental_health_assessment": {"response_mode": "crisis"},
        })
        self.assertIn("আপনাকে একা", result["answer"])
        self.assertIn("৯৯৯", result["answer"])

    def test_clean_llm_output_removes_na_and_fixes_markdown(self):
        sample = (
            "<think>Analyzing request...</think>\n"
            "•\n"
            "*Master's Degree Programs at Bangladesh University of Professionals (BUP)**\n"
            "•\n"
            "**Faculty of Arts & Social Sciences (FASS)**\n"
            "•\n"
            "**Master of Development Studies (MDS — Professional)**\n"
            "+ Type: Professional\n"
            "+ Schedule: Weekend (Fri & Sat)\n"
            "+ Duration: 1.5–2 Years\n"
            "+ Credits: 48\n"
            "•\n"
            "**Master of Laws (LLM — Professional)**\n"
            "+ Type: Professional\n"
            "+ Schedule: N/A\n"
            "+ Duration: N/A\n"
            "+ Credits: N/A\n"
            "+ Target Audience: N/A\n"
        )
        cleaned = clean_llm_output(sample)
        self.assertNotIn("<think>", cleaned)
        self.assertNotIn("+ Schedule: N/A", cleaned)
        self.assertNotIn("+ Duration: N/A", cleaned)
        self.assertNotIn("+ Credits: N/A", cleaned)
        self.assertNotIn("+ Target Audience: N/A", cleaned)
        self.assertIn("**Master's Degree Programs at Bangladesh University of Professionals (BUP)**", cleaned)
        self.assertIn("**Faculty of Arts & Social Sciences (FASS)**", cleaned)
        self.assertIn("+ Type: Professional", cleaned)
        self.assertIn("+ Duration: 1.5–2 Years", cleaned)

    def test_broad_masters_course_inquiries_expand_consistently(self):
        queries = [
            "i want to about the masters courses you offer..",
            "what are the masters courses offer by the bup",
            "bup has masters course",
            "what master courses do you have?",
        ]
        for q in queries:
            expanded = build_retrieval_question(q, [])
            self.assertEqual(
                expanded,
                "What master's programs does BUP offer?",
                f"Failed for query: {q}",
            )

    def test_contextual_discipline_follow_up_routing_and_expansion(self):
        masters_history = [
            {
                "question": "what are the masters courses offer by the bup",
                "answer": "BUP offers over 20+ Master's degree programs across 5 faculties. Which academic field interests you?",
            }
        ]
        # Follow-up "business" should route to rag when history is present
        self.assertTrue(is_contextual_follow_up("business", masters_history))
        self.assertEqual(route_question("business", conversation_history=masters_history), "rag")

        # Expansion should maintain context and specify Master's degree program
        expanded = build_retrieval_question("business", masters_history)
        self.assertIn("what are the masters courses offer by the bup", expanded)
        self.assertIn("BUP Master's degree program in business", expanded)

        # Similarly for "computer science"
        self.assertTrue(is_contextual_follow_up("computer science", masters_history))
        expanded_cs = build_retrieval_question("computer science", masters_history)
        self.assertIn("BUP Master's degree program in computer science", expanded_cs)

    def test_rag_prompt_contains_advisor_triage_guidelines(self):
        template = rag_prompt.template
        self.assertIn("20+ Master's degree programs across 5 faculties", template)
        self.assertIn("NO SPEC SHEET DUMPING", template)
        self.assertIn("STRICT BAN ON \"N/A\"", template)
        self.assertIn("MANDATORY CLARIFICATION QUESTION", template)
        self.assertIn("Which academic field or faculty interests you most", template)

    def test_undergraduate_and_phd_course_inquiries_expansion(self):
        ug_queries = [
            "what are the bachelor courses offered by bup?",
            "undergraduate programs in bup",
            "bup er bachelor courses ki ki?",
            "bachelor degree programs at bup",
        ]
        for q in ug_queries:
            expanded = build_retrieval_question(q, [])
            self.assertEqual(
                expanded,
                "What undergraduate bachelor degree programs does BUP offer?",
                f"Failed for query: {q}",
            )

        phd_queries = [
            "what mphil or phd programs does bup offer?",
            "phd courses in bup",
            "available phd programs",
        ]
        for q in phd_queries:
            expanded = build_retrieval_question(q, [])
            self.assertEqual(
                expanded,
                "What MPhil and PhD research degree programs does BUP offer?",
                f"Failed for query: {q}",
            )

    def test_language_enforcement_for_english_banglish_and_bengali(self):
        # English queries -> 'en' response in English
        self.assertEqual(response_language_code("what are the masters courses in bup?"), "en")
        self.assertIn("fluent English", response_language_instruction("what are the masters courses in bup?"))

        # Banglish queries -> 'en' response in English (no Banglish mirroring)
        self.assertEqual(response_language_code("bup er masters course gulo ki ki?"), "en")
        self.assertIn("fluent English", response_language_instruction("bup er masters course gulo ki ki?"))
        self.assertEqual(response_language_code("amar masters kora dorkar kon subject ache"), "en")
        self.assertIn("fluent English", response_language_instruction("amar masters kora dorkar kon subject ache"))

        # Bengali queries (in Bengali script) -> 'bn' response in Bengali
        self.assertEqual(response_language_code("বিউপি তে কি কি মাস্টার্স কোর্স আছে?"), "bn")
        self.assertIn("Bangla using Bengali script", response_language_instruction("বিউপি তে কি কি মাস্টার্স কোর্স আছে?"))
        self.assertEqual(response_language_code("মাস্টার্স কোর্সের তালিকা দিন"), "bn")
        self.assertIn("Bangla using Bengali script", response_language_instruction("মাস্টার্স কোর্সের তালিকা দিন"))

    def test_broad_admission_intent_clarifies_level(self):
        self.assertEqual(route_question("i would like to take admission"), "clarify")
        self.assertEqual(route_question("I want to get admitted to BUP"), "clarify")

    def test_high_school_and_twelfth_pass_expands_to_undergraduate(self):
        queries = [
            "what is you courses offered for a 12th pass student?",
            "courses offered for 12th pass student",
            "what courses are offered after 12th?",
            "undergradute",
            "bup bachelor courses",
        ]
        for q in queries:
            expanded = build_retrieval_question(q, [])
            self.assertEqual(
                expanded,
                "What undergraduate bachelor degree programs does BUP offer?",
                f"Failed for query: {q}",
            )

    def test_science_background_twelfth_pass_expands_to_science_undergrad(self):
        queries = [
            "what courses are offered for class 12 science student?",
            "admission after 12 completed and science",
        ]
        for q in queries:
            expanded = build_retrieval_question(q, [])
            self.assertEqual(
                expanded,
                "What undergraduate bachelor degree programs are offered for science background students at BUP?",
                f"Failed for query: {q}",
            )

    def test_twelfth_completed_and_science_follow_up(self):
        history = [
            {"question": "i would like to take admission", "answer": "Sure. BUP admission depends on the program level. Which one are you interested in? 1. Undergraduate 2. Master's 3. MPhil / PhD"},
            {"question": "undergradute", "answer": "BUP offers 16 undergraduate bachelor's degree programs across 4 faculties."},
        ]
        expanded = build_retrieval_question("12 completed and science", history)
        self.assertEqual(
            expanded,
            "What undergraduate bachelor degree programs are offered for science background students at BUP?",
        )

    def test_undergraduate_specific_fee_question_preserved(self):
        q = "what is the admission form fee for bachelor programme?"
        self.assertEqual(route_question(q), "rag")
        self.assertEqual(build_retrieval_question(q, []), q)

    def test_discipline_admission_criteria_routes_to_rag_not_clarify(self):
        cse_history = [
            {
                "question": "i want to know details about computer science",
                "answer": "The FST department at BUP offers B.Sc. in Computer Science and Engineering (CSE).",
            }
        ]
        self.assertEqual(
            route_question(
                "Artificial intelligence, what is the admission criteria i need to meet.",
                conversation_history=cse_history,
            ),
            "rag",
        )

    def test_redesigned_student_journey_and_privacy_routing(self):
        self.assertEqual(
            route_question("can you show my friend saad bin sakib cgpa?", is_authenticated=True),
            "student",
        )
        self.assertEqual(route_question("what is my total cgpa?", is_authenticated=True), "student")
        self.assertEqual(route_question("do i have any due?", is_authenticated=True), "student")
        self.assertEqual(route_question("who is my academic advisor?", is_authenticated=True), "student")
        self.assertEqual(route_question("what is my attendance percentage?", is_authenticated=True), "student")
        self.assertEqual(route_question("what is my total cgpa?", is_authenticated=False), "auth_required")

    def test_computer_science_follow_up_not_collapsed_to_generic_science(self):
        ug_history = [
            {
                "question": "what are the bachelor course bup offers?",
                "answer": "BUP offers 16 undergraduate Bachelor's degree programs across 4 primary faculties.",
            }
        ]
        expanded = build_retrieval_question("i would like to about computer science..", ug_history)
        self.assertIn("computer science", expanded.lower())
        self.assertNotIn("science background students", expanded.lower())

    def test_banglish_and_bengali_distress_and_crisis_routing(self):
        self.assertEqual(route_question("amar bachte iccha korche na"), "mental_support")
        self.assertEqual(
            route_question("আমার খুব মানসিক চাপ লাগছে, মনে হচ্ছে পড়াশোনা আর চালিয়ে যেতে পারব না"),
            "mental_support",
        )

    def test_student_record_and_identity_break_out_of_mental_support_loop(self):
        support_history = [
            {
                "question": "i should dropout... i can't bear it anymore",
                "answer": "I can see that you're feeling like you're at your breaking point. What's driving you to feel this way?",
            }
        ]
        stale_assessment = {"response_mode": "crisis", "risk_level": "critical"}
        self.assertEqual(
            route_question(
                "can you fetch my cgpa?",
                is_authenticated=True,
                conversation_history=support_history,
                mental_health_assessment=stale_assessment,
            ),
            "student",
        )
        self.assertEqual(
            route_question(
                "i forgot about my first semester cgpa. can you fetch it..?",
                is_authenticated=True,
                conversation_history=support_history,
                mental_health_assessment=stale_assessment,
            ),
            "student",
        )
        self.assertEqual(
            route_question(
                "do you know me?",
                is_authenticated=True,
                conversation_history=support_history,
                mental_health_assessment=stale_assessment,
            ),
            "student",
        )


if __name__ == "__main__":
    unittest.main()
