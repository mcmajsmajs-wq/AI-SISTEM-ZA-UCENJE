import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, ANY
from sqlalchemy.orm import Session

from app.services.flashcard import (
    sm2_calculate, create_deck, list_decks, get_deck,
    delete_deck, add_card, add_cards_batch, get_due_cards,
    review_card, generate_from_document, _extract_keywords_auto, _split_sentences
)
from app.services.quiz.helpers.selection import is_chunk_quality
from app.db.models.flashcard import Deck, Flashcard, ReviewLog
from app.db.models.user import User
from app.schemas.flashcard import (
    DeckCreate, FlashcardCreate, ReviewRequest
)


class TestSM2Algorithm:
    def test_sm2_first_quality_5(self):
        result = sm2_calculate(quality=5, repetitions=0, ease_factor=2.5, interval=0)
        assert result["repetitions"] == 1
        assert result["interval"] == 1
        assert result["ease_factor"] == 2.6

    def test_sm2_second_quality_4(self):
        result = sm2_calculate(quality=4, repetitions=1, ease_factor=2.6, interval=1)
        assert result["repetitions"] == 2
        assert result["interval"] == 6
        assert result["ease_factor"] == 2.6

    def test_sm2_third_review(self):
        result = sm2_calculate(quality=5, repetitions=2, ease_factor=2.6, interval=6)
        assert result["repetitions"] == 3
        assert result["interval"] == round(6 * 2.6)
        assert result["ease_factor"] == 2.7

    def test_sm2_quality_0_resets(self):
        result = sm2_calculate(quality=0, repetitions=5, ease_factor=2.5, interval=100)
        assert result["repetitions"] == 0
        assert result["interval"] == 1

    def test_sm2_quality_1_resets(self):
        result = sm2_calculate(quality=1, repetitions=3, ease_factor=2.5, interval=30)
        assert result["repetitions"] == 0
        assert result["interval"] == 1

    def test_sm2_quality_2_resets(self):
        result = sm2_calculate(quality=2, repetitions=10, ease_factor=2.5, interval=365)
        assert result["repetitions"] == 0
        assert result["interval"] == 1

    def test_sm2_quality_3_minimum_pass(self):
        result = sm2_calculate(quality=3, repetitions=0, ease_factor=2.5, interval=0)
        assert result["repetitions"] == 1
        assert result["interval"] == 1
        assert result["ease_factor"] == pytest.approx(2.36, rel=1e-2)

    def test_sm2_ef_clamping(self):
        result = sm2_calculate(quality=3, repetitions=0, ease_factor=1.2, interval=0)
        assert result["ease_factor"] >= 1.3

    def test_sm2_ef_delayed_next_interval(self):
        result = sm2_calculate(quality=5, repetitions=5, ease_factor=2.5, interval=60)
        assert result["repetitions"] == 6
        expected = round(60 * 2.6)
        assert result["interval"] == expected


class TestDeckCrud:
    def test_list_decks(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        user_id = uuid4()
        result = list_decks(db=mock_db, user_id=user_id)
        assert result == []

    def test_create_deck_basic(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()

        mocker.patch("app.services.flashcard.Deck", side_effect=lambda **kw: MagicMock(spec=Deck, **kw))

        result = create_deck(db=mock_db, user_id=user_id, name="Test Deck")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_deck_with_description(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()
        name = "Test Deck"
        description = "A test deck"

        result = create_deck(db=mock_db, user_id=user_id, name=name, description=description)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_deck_found(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(spec=Deck, id=uuid4(), name="Found")

        result = get_deck(db=mock_db, deck_id=uuid4(), user_id=uuid4())
        assert result is not None

    def test_get_deck_not_found(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = get_deck(db=mock_db, deck_id=uuid4(), user_id=uuid4())
        assert result is None

    def test_get_deck_wrong_user(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = get_deck(db=mock_db, deck_id=uuid4(), user_id=uuid4())
        assert result is None

    def test_list_decks_returns_decks(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            MagicMock(spec=Deck, id=uuid4(), name="A"),
            MagicMock(spec=Deck, id=uuid4(), name="B"),
        ]

        decks = list_decks(db=mock_db, user_id=uuid4())
        assert len(decks) == 2

    def test_delete_deck(self, mocker):
        mock_db = MagicMock(spec=Session)
        deck_id = uuid4()
        user_id = uuid4()

        mock_deck = MagicMock(spec=Deck)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_deck

        result = delete_deck(db=mock_db, deck_id=deck_id, user_id=user_id)
        assert result is True
        mock_db.delete.assert_called_once_with(mock_deck)
        mock_db.commit.assert_called_once()

    def test_delete_deck_not_found(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = delete_deck(db=mock_db, deck_id=uuid4(), user_id=uuid4())
        assert result is False

    def test_delete_deck_wrong_user(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = delete_deck(db=mock_db, deck_id=uuid4(), user_id=uuid4())
        assert result is False


class TestFlashcardCrud:
    def test_add_card(self, mocker):
        mock_db = MagicMock(spec=Session)

        add_card(db=mock_db, deck_id=uuid4(), front="Front", back="Back")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_add_cards_batch(self, mocker):
        mock_db = MagicMock(spec=Session)
        deck_id = uuid4()
        cards_data = [
            {"front": "F1", "back": "B1"},
            {"front": "F2", "back": "B2"},
        ]

        result = add_cards_batch(db=mock_db, deck_id=deck_id, cards=cards_data)

        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 1
        assert len(result) == 2


class TestReviewFlow:
    def test_review_card_first_time(self, mocker):
        mock_db = MagicMock(spec=Session)
        card_id = uuid4()
        user_id = uuid4()

        mock_card = MagicMock(spec=Flashcard, id=card_id, deck_id=uuid4())
        mock_card.repetitions = 0
        mock_card.ease_factor = 2.5
        mock_card.interval = 0
        mock_deck = MagicMock(spec=Deck, id=uuid4())
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        mock_query.first.side_effect = [mock_card, mock_deck, None, mock_user]

        mocker.patch("app.services.flashcard.award_xp",
                     return_value={"xp_awarded": 25, "total_xp": 100, "level": 2,
                                   "leveled_up": False, "new_badges": []})
        mocker.patch("app.services.flashcard.update_streak",
                     return_value={"streak": 1, "new_badges": []})

        result = review_card(db=mock_db, card_id=card_id, user_id=user_id, quality=5)

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_review_card_nonexistent(self, mocker):
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Card not found"):
            review_card(db=mock_db, card_id=uuid4(), user_id=uuid4(), quality=3)

    def test_review_card_wrong_user(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_b = uuid4()

        mock_card = MagicMock(spec=Flashcard, id=uuid4(), deck_id=uuid4())
        mock_card.repetitions = 0
        mock_card.ease_factor = 2.5
        mock_card.interval = 0

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        mock_query.first.side_effect = [mock_card, None]

        with pytest.raises(PermissionError):
            review_card(db=mock_db, card_id=uuid4(), user_id=user_b, quality=3)

    def test_review_card_low_quality_resets(self, mocker):
        mock_db = MagicMock(spec=Session)
        card_id = uuid4()
        user_id = uuid4()

        mock_card = MagicMock(spec=Flashcard, id=card_id, deck_id=uuid4())
        mock_card.repetitions = 5
        mock_card.interval = 100
        mock_card.ease_factor = 2.5
        mock_deck = MagicMock(spec=Deck, id=uuid4())
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        mock_query.first.side_effect = [mock_card, mock_deck, None, mock_user]

        mocker.patch("app.services.flashcard.award_xp",
                     return_value={"xp_awarded": 0, "total_xp": 100, "level": 2,
                                   "leveled_up": False, "new_badges": []})
        mocker.patch("app.services.flashcard.update_streak",
                     return_value={"streak": 1, "new_badges": []})

        result = review_card(db=mock_db, card_id=card_id, user_id=user_id, quality=0)

        assert result["repetitions"] == 0
        assert result["interval"] == 1


class TestDueCards:
    def test_due_cards_empty_when_no_cards(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()

        mocker.patch.object(mock_db.query.return_value, "join",
                            return_value=mock_db.query.return_value)
        mocker.patch.object(mock_db.query.return_value, "filter",
                            return_value=mock_db.query.return_value)
        mocker.patch.object(mock_db.query.return_value, "order_by",
                            return_value=mock_db.query.return_value)
        mocker.patch.object(mock_db.query.return_value, "limit",
                            return_value=mock_db.query.return_value)
        mock_db.query.return_value.all.return_value = []

        due = get_due_cards(db=mock_db, user_id=user_id, limit=10)
        assert due == []


class TestGenerateFromDocument:
    def test_generate_from_document_no_chunks(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.user_id = user_id

        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with pytest.raises(ValueError, match="has no chunks"):
            generate_from_document(db=mock_db, user_id=user_id, document_id=doc_id, mode="auto")

    def test_generate_from_document_auto(self, mocker):
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.user_id = user_id

        mock_chunk = MagicMock()
        mock_chunk.id = uuid4()
        mock_chunk.content = "This is a **bold** term with important context."

        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_chunk]

        mocker.patch("app.services.flashcard.create_deck", return_value=MagicMock(id=uuid4(), name="Auto-generated"))
        mocker.patch("app.services.flashcard.add_cards_batch", return_value=[])

        result = generate_from_document(db=mock_db, user_id=user_id, document_id=doc_id, mode="auto")
        assert result is not None


class TestChunkQualityFilter:
    """Test that metadata chunks are filtered out for both Serbian and English content."""

    def test_empty_chunk_filtered(self):
        assert not is_chunk_quality("")

    def test_too_short_chunk_filtered(self):
        assert not is_chunk_quality("Hi there")

    def test_serbian_cip_filtered(self):
        text = "Народна библиотека Србије, Београд\n37.016:94(075.2)\nСТОЈАНОВИЋ, Александар"
        assert not is_chunk_quality(text)

    def test_serbian_title_page_filtered(self):
        text = "Др Александар Стојановић\nИСТОРИЈА 8\nУџбеник са одабраним историјским изворима"
        assert not is_chunk_quality(text)

    def test_serbian_editorial_filtered(self):
        text = "Аутор\nРецензенти\nГлавни уредник\nПредметни уредник\nИлустрације\nЛектура и коректура"
        assert not is_chunk_quality(text)

    def test_serbian_toc_filtered(self):
        assert not is_chunk_quality("САДРЖАЈ\n1. Увод\n2. Први светски рат")

    def test_english_publisher_filtered(self):
        assert not is_chunk_quality("Published by Manning Publications Co.")

    def test_english_cip_filtered(self):
        assert not is_chunk_quality("Library of Congress Cataloging-in-Publication Data")

    def test_english_translator_filtered(self):
        assert not is_chunk_quality("Translated by Thomas Cleary\nWith an Introduction by Lionel Giles")

    def test_english_copyright_filtered(self):
        assert not is_chunk_quality("All rights reserved. No part of this publication may be reproduced.")

    def test_content_chunk_passes(self):
        assert is_chunk_quality("Venice Film Festival, one of the most prestigious in the world, was first held in 1932. Charlie Chaplin was one of the greatest actors in film history.")

    def test_serbian_content_chunk_passes(self):
        assert is_chunk_quality("Од првих дана постојања ове партије, њени чланови били су склони насиљу. На чело партије дошао је Адолф Хитлер.")


class TestAutoModeQuestionQuality:
    """Test that auto mode produces complete questions, not single-word fronts."""

    def test_fallback_creates_complete_front(self):
        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        text = "Од првих дана постојања ове партије, њени чланови били су склони насиљу, тучама и физичком обрачунавању са политичким противницима. На чело партије дошао је Адолф Хитлер."
        chunks = [Chunk(id="t1", content=text, sequence_number=1, document_id="d1")]
        cards = _extract_keywords_auto(chunks, max_cards=4)
        assert len(cards) > 0
        for c in cards:
            assert len(c["front"]) > 10, f"Front too short: {c['front']}"
            assert len(c["back"]) > 10, f"Back too short: {c['back']}"

    def test_fallback_splits_by_comma(self):
        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        text = "Венецијански филмски фестивал, један од најзначајнијих у свету са наградом Златни лав, први пут је одржан 1932. Чарлс Чаплин је био један од највећих глумаца."
        chunks = [Chunk(id="t2", content=text, sequence_number=1, document_id="d2")]
        cards = _extract_keywords_auto(chunks, max_cards=2)
        assert len(cards) > 0
        first_front = cards[0]["front"]
        assert len(first_front) > 15, f"Comma-split front too short: {first_front}"

    def test_fallback_english_content(self):
        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        text = "Venice Film Festival, one of the most prestigious in the world with its Golden Lion award, was first held in 1932. Charlie Chaplin was one of the greatest actors and directors in film history."
        chunks = [Chunk(id="t3", content=text, sequence_number=1, document_id="d3")]
        cards = _extract_keywords_auto(chunks, max_cards=4)
        assert len(cards) > 0
        for c in cards:
            assert len(c["front"]) > 10, f"English front too short: {c['front']}"
            assert len(c["back"]) > 10, f"English back too short: {c['back']}"

    def test_quoted_terms_extracted(self):
        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        text = 'Венецијански филмски фестивал, са наградом "Златни лав", први пут је одржан 1932. Његов лик "Скитнице" постао је симбол.'
        chunks = [Chunk(id="t4", content=text, sequence_number=1, document_id="d4")]
        cards = _extract_keywords_auto(chunks, max_cards=4)
        assert len(cards) > 0
        # Should find quoted terms as card fronts
        fronts = [c["front"] for c in cards]
        assert any("Златни" in f for f in fronts) or any("Скитнице" in f for f in fronts)


class TestSplitSentences:
    """Test sentence splitting for Serbian/English text."""

    def test_serbian_sentences(self):
        text = "Прва реченица. Друга реченица! Трећа реченица?"
        result = _split_sentences(text)
        assert len(result) == 3

    def test_english_sentences(self):
        text = "First sentence. Second sentence! Third sentence?"
        result = _split_sentences(text)
        assert len(result) == 3

    def test_ellipsis_handling(self):
        text = "Prvi deo... Drugi deo. Treći deo."
        result = _split_sentences(text)
        assert len(result) >= 2

    def test_single_sentence(self):
        text = "Just one sentence here."
        result = _split_sentences(text)
        assert len(result) == 1

    def test_empty_text(self):
        assert _split_sentences("") == []


class TestAIGenerationErrorHandling:
    """Test that AI generation errors are properly wrapped with meaningful messages."""

    def test_generate_from_document_no_chunks(self):
        """Should raise ValueError when document has no chunks."""
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        with pytest.raises(ValueError, match="has no chunks"):
            generate_from_document(db=mock_db, user_id=uuid4(), document_id=uuid4(), mode="auto")

    def test_generate_from_document_handles_api_errors(self, mocker):
        """The generate_from_document service should catch and wrap API errors."""
        mock_db = MagicMock(spec=Session)
        user_id = uuid4()
        doc_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.user_id = user_id

        mock_chunk = MagicMock()
        mock_chunk.id = uuid4()
        mock_chunk.content = "Some content for testing."

        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_chunk]

        mocker.patch("app.services.flashcard._generate_with_ai", side_effect=ValueError("API key not configured"))
        mocker.patch("app.services.flashcard.create_deck", return_value=MagicMock(id=uuid4(), name="Test"))
        mocker.patch("app.services.flashcard.add_cards_batch", return_value=[])

        with pytest.raises(ValueError, match="API ključ"):
            generate_from_document(db=mock_db, user_id=user_id, document_id=doc_id, mode="ai")


class TestCrewAIQuizQuestionFlow:
    """Test CrewAI quiz question generation."""

    def test_quiz_question_flow_can_be_created(self):
        """Verify QuizQuestionFlow can be created with the same LLM."""
        from app.services.crewai_flashcard import (
            _create_crewai_llm, QuizQuestionFlow, PROVIDER_LLM_CONFIG
        )

        llm = _create_crewai_llm("openai", "sk-test-key")
        flow = QuizQuestionFlow(llm=llm, text="Some educational text", num_questions=5)
        assert flow is not None
        assert flow.num_questions == 5
        assert flow.llm is llm
        assert flow.text == "Some educational text"

    def test_quiz_question_flow_returns_valid_question_format(self, mocker):
        """Verify the flow returns valid question objects."""
        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        expected_questions = [
            {
                "question_text": "What is photosynthesis?",
                "question_type": "multiple_choice",
                "options": ["A) Process by which plants convert sunlight into energy",
                            "B) Process by which animals breathe"],
                "correct_answer": "A",
                "explanation": "Photosynthesis converts light energy into chemical energy.",
                "points": 1,
                "order_index": 0,
            },
            {
                "question_text": "Is photosynthesis unique to plants?",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "Only plants perform photosynthesis.",
                "points": 1,
                "order_index": 1,
            },
        ]

        with mocker.patch(
            "app.services.crewai_flashcard.QuizQuestionFlow.kickoff",
            return_value=expected_questions,
        ) as mock_kickoff:
            questions = generate_quiz_questions_with_crewai(
                text="Some educational text about photosynthesis.",
                provider="openai",
                api_key="sk-test-key",
                num_questions=5,
            )

        assert len(questions) == 2
        for q in questions:
            assert "question_text" in q
            assert "question_type" in q
            assert "correct_answer" in q
            assert "explanation" in q
            assert q["question_type"] in ("multiple_choice", "true_false", "fill_blank")
            assert len(q["question_text"]) > 0

    def test_quiz_question_types_are_valid(self):
        """Verify question types from the validator are valid schema types."""
        from app.services.quiz.helpers.parsing import _validate_questions

        questions = [
            {
                "question_text": "What is 2+2?",
                "question_type": "multiple_choice",
                "options": ["3", "4", "5"],
                "correct_answer": "4",
                "explanation": "Basic math.",
            },
            {
                "question_text": "Is the sky blue?",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "The sky appears blue.",
            },
            {
                "question_text": "The capital of France is __",
                "question_type": "fill_blank",
                "correct_answer": "Paris",
                "explanation": "Paris is the capital of France.",
            },
        ]

        validated = _validate_questions(questions)
        assert len(validated) == 3
        assert validated[0]["question_type"] == "multiple_choice"
        assert validated[1]["question_type"] == "true_false"
        assert validated[2]["question_type"] == "fill_blank"
        assert all(q.get("order_index") is not None for q in validated)

    def test_quiz_question_flow_respects_num_questions_limit(self, mocker):
        """Verify the flow limits questions to num_questions."""
        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        many_questions = [
            {
                "question_text": f"Question {i}",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "Test.",
            }
            for i in range(10)
        ]

        with mocker.patch(
            "app.services.crewai_flashcard.QuizQuestionFlow.kickoff",
            return_value=many_questions,
        ):
            questions = generate_quiz_questions_with_crewai(
                text="Some text",
                provider="openai",
                api_key="sk-test-key",
                num_questions=3,
            )

        assert len(questions) <= 3

    def test_generate_quiz_questions_raises_without_api_key(self):
        """Verify error when no API key is provided."""
        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        with pytest.raises(ValueError, match="API ključ"):
            generate_quiz_questions_with_crewai(
                text="Some text",
                provider="openai",
                api_key=None,
                num_questions=5,
            )

    def test_crewai_quiz_fallback_in_generation_module(self, mocker):
        """Verify fallback when CrewAI quiz generation raises an error."""
        from app.services.quiz.generation import _generate_with_crewai_questions

        text = "Photosynthesis is the process by which plants convert sunlight into energy. This process occurs in the chloroplasts of plant cells. The main inputs are carbon dioxide, water, and sunlight."

        questions, provider = _generate_with_crewai_questions(
            text=text,
            num_questions=2,
            provider=None,
        )[1:]

        assert len(questions) > 0
        assert provider == "fallback"

    def test_crewai_quiz_fallback_without_api_key(self, mocker):
        """Verify fallback when API key is missing."""
        from app.services.quiz.generation import _generate_with_crewai_questions

        text = "Photosynthesis is the process by which plants convert sunlight into energy. This process occurs in the chloroplasts of plant cells."

        questions, provider = _generate_with_crewai_questions(
            text=text,
            num_questions=2,
            provider="openai",
            user_openai_key=None,
        )[1:]

        assert len(questions) > 0
        assert provider == "fallback"


class TestCrewAIIntegration:
    """Test CrewAI flashcard generation and fallback."""

    def test_crewai_flow_agents_can_be_created(self):
        """Verify CrewAI agents can be created with the same LLM."""
        from app.services.crewai_flashcard import (
            _create_crewai_llm, FlashcardFlow, PROVIDER_LLM_CONFIG
        )
        from collections import namedtuple

        llm = _create_crewai_llm("openai", "sk-test-key")
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        chunks = [
            Chunk(
                id="c1",
                content="Photosynthesis is the process by which plants convert sunlight into energy.",
                sequence_number=1,
                document_id="d1",
            )
        ]
        flow = FlashcardFlow(llm=llm, chunks=chunks, max_cards=5)
        assert flow is not None
        assert flow.max_cards == 5
        assert flow.llm is llm

    def test_crewai_fallback_when_provider_fails(self, mocker):
        """Verify fallback to old _generate_with_ai when CrewAI fails."""
        from app.services.flashcard import _generate_with_ai
        from unittest.mock import MagicMock, patch

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.ai_api_key_openai = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        chunks = [
            Chunk(
                id="c1",
                content="Photosynthesis converts sunlight into chemical energy.",
                sequence_number=1,
                document_id="d1",
            )
        ]

        with patch(
            "app.services.crewai_flashcard.generate_with_crewai",
            side_effect=RuntimeError("CrewAI failed"),
        ):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_choice = MagicMock()
                mock_choice.message.content = (
                    '[{"front": "What is photosynthesis?", '
                    '"back": "It converts sunlight into energy."}]'
                )
                mock_client.chat.completions.create.return_value = MagicMock(
                    choices=[mock_choice]
                )

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.OPENAI_API_KEY = "sk-test"
                    cards, method = _generate_with_ai(
                        chunks=chunks,
                        provider="openai",
                        user_id="user-1",
                        db=mock_db,
                        max_cards=5,
                    )

        assert len(cards) == 1
        assert cards[0]["front"] == "What is photosynthesis?"
        assert method == "openai"

    def test_crewai_flow_returns_valid_format(self, mocker):
        """Verify that the CrewAI flow entry point returns valid flashcard format."""
        from app.services.crewai_flashcard import generate_with_crewai
        from unittest.mock import MagicMock, patch

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.ai_api_key_openai = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        from collections import namedtuple
        Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
        chunks = [
            Chunk(
                id="c1",
                content="Paris is the capital of France. It is known for the Eiffel Tower.",
                sequence_number=1,
                document_id="d1",
            )
        ]

        expected_cards = [
            {"front": "What is the capital of France?", "back": "Paris is the capital of France."},
            {"front": "What is Paris known for?", "back": "Paris is known for the Eiffel Tower."},
        ]

        with patch(
            "app.services.crewai_flashcard.FlashcardFlow.kickoff",
            return_value=expected_cards,
        ) as mock_kickoff:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "sk-test"
                cards = generate_with_crewai(
                    chunks=chunks,
                    provider="openai",
                    user_id="user-1",
                    db=mock_db,
                    max_cards=5,
                )

        assert len(cards) == 2
        for card in cards:
            assert "front" in card
            assert "back" in card
            assert "source_chunk_id" in card
            assert len(card["front"]) > 0
            assert len(card["back"]) > 0
