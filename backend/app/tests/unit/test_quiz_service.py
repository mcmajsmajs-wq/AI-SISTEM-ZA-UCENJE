# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE UNIT TESTS
================================================================================
Testovi za generisanje i validaciju kviz pitanja.

Pokretanje:
    pytest tests/unit/test_quiz_service.py -v
================================================================================
"""

import pytest
import json


class TestValidateQuestions:
    """Testovi za _validate_questions() — filtriranje i sanitizacija pitanja."""

    def _validate(self, data):
        from app.services.quiz import _validate_questions

        return _validate_questions(data)

    def test_valid_multiple_choice_passes(self):
        """Validno multiple_choice pitanje mora proći."""
        questions = [
            {
                "question_text": "What is LightBurn?",
                "question_type": "multiple_choice",
                "options": [
                    "A laser control software for cutting and engraving",
                    "A photo editing application",
                    "A 3D modeling tool",
                    "A vector graphics converter",
                ],
                "correct_answer": "A laser control software for cutting and engraving",
                "explanation": "LightBurn is laser control software.",
                "points": 1,
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1
        assert result[0]["question_type"] == "multiple_choice"

    def test_valid_true_false_passes(self):
        """Validno true_false pitanje mora proći."""
        questions = [
            {
                "question_text": "Is LightBurn free?",
                "question_type": "true_false",
                "options": ["Tačno", "Netačno"],
                "correct_answer": "Netačno",
                "explanation": "LightBurn requires a paid license.",
                "points": 1,
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1

    def test_valid_checkbox_passes(self):
        """Validno checkbox pitanje sa 2+ tačnih odgovora mora proći."""
        questions = [
            {
                "question_text": "Which are valid laser modes?",
                "question_type": "checkbox",
                "options": [
                    "Fill mode for engraving",
                    "Line mode for cutting",
                    "Offset mode for outlines",
                    "Spiral mode for decorative cuts",
                ],
                "correct_answer": "Fill mode for engraving,Line mode for cutting",
                "explanation": "Fill and Line are the primary laser modes.",
                "points": 2,
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1
        assert result[0]["question_type"] == "checkbox"
        assert result[0]["points"] == 2

    def test_letter_only_options_rejected(self):
        """Pitanja sa opcijama kao slova (A, B, C, D) moraju biti odbačena."""
        questions = [
            {
                "question_text": "What does LightBurn do?",
                "question_type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "A is correct.",
                "points": 1,
            }
        ]
        result = self._validate(questions)
        assert len(result) == 0, "Pitanja sa samo-slova opcijama moraju biti odbačena"

    def test_missing_required_field_skipped(self):
        """Pitanje bez obaveznog polja mora biti preskočeno."""
        questions = [
            {
                "question_text": "What is this?",
                # missing question_type, options, correct_answer
            }
        ]
        result = self._validate(questions)
        assert len(result) == 0

    def test_checkbox_with_one_correct_downgraded_to_multiple_choice(self):
        """Checkbox sa samo 1 tačnim odgovorom mora biti konvertovano u multiple_choice."""
        questions = [
            {
                "question_text": "Which is correct?",
                "question_type": "checkbox",
                "options": [
                    "Option A text",
                    "Option B text",
                    "Option C text",
                    "Option D text",
                ],
                "correct_answer": "Option A text",  # only 1 correct — wrong for checkbox
                "explanation": "Option A is the only correct one.",
                "points": 1,
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1
        assert result[0]["question_type"] == "multiple_choice"

    def test_checkbox_points_upgraded_to_minimum_2(self):
        """Checkbox pitanje sa points=1 mora biti povećano na points=2."""
        questions = [
            {
                "question_text": "Select all correct options:",
                "question_type": "checkbox",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A,Option C",
                "explanation": "A and C are correct.",
                "points": 1,  # should be auto-upgraded
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1
        assert result[0]["points"] == 2

    def test_order_index_assigned(self):
        """order_index mora biti dodeljen prema poziciji u listi."""
        questions = [
            {
                "question_text": f"Question {i}?",
                "question_type": "true_false",
                "options": ["Tačno", "Netačno"],
                "correct_answer": "Tačno",
                "explanation": "Explanation",
                "points": 1,
            }
            for i in range(3)
        ]
        result = self._validate(questions)
        assert len(result) == 3
        for i, q in enumerate(result):
            assert q["order_index"] == i

    def test_explanation_defaults_to_empty_string(self):
        """explanation polje mora biti postavljeno na prazan string ako nedostaje."""
        questions = [
            {
                "question_text": "What is correct?",
                "question_type": "true_false",
                "options": ["Tačno", "Netačno"],
                "correct_answer": "Tačno",
                # no explanation field
            }
        ]
        result = self._validate(questions)
        assert len(result) == 1
        assert result[0]["explanation"] == ""

    def test_non_dict_items_skipped(self):
        """Elementi koji nisu dict moraju biti preskočeni."""
        data = [
            "not a dict",
            None,
            {
                "question_text": "Valid?",
                "question_type": "true_false",
                "options": ["Tačno", "Netačno"],
                "correct_answer": "Tačno",
            },
        ]
        result = self._validate(data)
        assert len(result) == 1


class TestQuizPrompt:
    """Testovi za QUIZ_PROMPT sadržaj i format."""

    def test_prompt_does_not_use_letter_only_examples(self):
        """QUIZ_PROMPT ne sme koristiti 'A', 'B', 'C', 'D' kao primere opcija."""
        from app.services.quiz import QUIZ_PROMPT

        # Format the prompt with dummy values to check its content
        formatted = QUIZ_PROMPT.format(num_questions=5, text="sample text")
        # Should NOT contain single-letter options in examples
        assert '"options": ["A", "B", "C", "D"]' not in formatted, (
            "QUIZ_PROMPT ne sme koristiti placeholder slova kao opcije — zbunjuje AI"
        )

    def test_prompt_mentions_all_question_types(self):
        """QUIZ_PROMPT mora da pominje sva 3 tipa pitanja."""
        from app.services.quiz import QUIZ_PROMPT

        assert "multiple_choice" in QUIZ_PROMPT
        assert "true_false" in QUIZ_PROMPT
        assert "checkbox" in QUIZ_PROMPT

    def test_prompt_mentions_checkbox_distribution(self):
        """QUIZ_PROMPT mora da instruira AI da generiše checkbox pitanja (ne samo opciono)."""
        from app.services.quiz import QUIZ_PROMPT

        # Should explicitly mention 30% or similar for checkbox
        assert "checkbox" in QUIZ_PROMPT
        assert "select all" in QUIZ_PROMPT.lower() or "select ALL" in QUIZ_PROMPT

    def test_prompt_mentions_full_text_options(self):
        """QUIZ_PROMPT mora da instruira AI da koristi pun tekst za opcije."""
        from app.services.quiz import QUIZ_PROMPT

        # Prompt should mention having multiple options (not single letters A,B,C,D)
        assert "4 plausible options" in QUIZ_PROMPT or "4 options" in QUIZ_PROMPT


class TestCheckAnswerLogic:
    """Testovi za logiku provere tačnosti odgovora za sve tipove pitanja."""

    def _check(self, q_type, user_answer, correct_answer):
        from app.services.quiz import QuizService

        return QuizService._check_answer_static(q_type, user_answer, correct_answer)

    def test_multiple_choice_correct(self):
        result = self._check(
            "multiple_choice", "Laser control software", "Laser control software"
        )
        assert result is True

    def test_multiple_choice_wrong(self):
        result = self._check(
            "multiple_choice", "Photo editor", "Laser control software"
        )
        assert result is False

    def test_multiple_choice_case_insensitive(self):
        result = self._check(
            "multiple_choice", "laser control software", "Laser control software"
        )
        assert result is True

    def test_true_false_correct(self):
        result = self._check("true_false", "Tačno", "Tačno")
        assert result is True

    def test_true_false_wrong(self):
        result = self._check("true_false", "Netačno", "Tačno")
        assert result is False

    def test_checkbox_all_correct(self):
        """Checkbox je tačan samo kad je TAČNO isti skup odgovora izabran."""
        result = self._check("checkbox", "Option A,Option C", "Option A,Option C")
        assert result is True

    def test_checkbox_order_independent(self):
        """Checkbox odgovor mora biti tačan bez obzira na redosled selekcije."""
        result = self._check("checkbox", "Option C,Option A", "Option A,Option C")
        assert result is True

    def test_checkbox_partial_wrong(self):
        """Checkbox je pogrešan ako korisnik izabere samo neke od tačnih odgovora."""
        result = self._check("checkbox", "Option A", "Option A,Option C")
        assert result is False

    def test_checkbox_extra_wrong(self):
        """Checkbox je pogrešan ako korisnik izabere više od tačnih odgovora."""
        result = self._check(
            "checkbox", "Option A,Option B,Option C", "Option A,Option C"
        )
        assert result is False
