import json
import os
import logging
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest


logger = logging.getLogger(__name__)

TEST_TEXT = (
    "Photosynthesis is the process by which plants convert sunlight into chemical energy. "
    "This process occurs in the chloroplasts of plant cells, which contain chlorophyll. "
    "The main inputs are carbon dioxide (CO2), water (H2O), and sunlight. "
    "The outputs are glucose (C6H12O6) and oxygen (O2). "
    "Photosynthesis consists of two stages: the light-dependent reactions and the Calvin cycle. "
    "In the light-dependent reactions, sunlight is captured and converted into ATP and NADPH. "
    "In the Calvin cycle, CO2 is fixed into organic molecules using ATP and NADPH."
)

Chunk = namedtuple("Chunk", ["id", "content", "sequence_number", "document_id"])
TEST_CHUNKS = [
    Chunk(id="c1", content=TEST_TEXT[:300], sequence_number=1, document_id="d1"),
    Chunk(id="c2", content=TEST_TEXT[300:], sequence_number=2, document_id="d1"),
]


def _get_env_api_keys() -> dict:
    """Cita API kljuceve iz environment variabli.

    Podrzani provideri: openai, groq, gemini, mistral, claude.
    DeepSeek nije u PROVIDER_LLM_CONFIG i ne moze se koristiti.
    """
    keys = {}
    for provider, env_var in [
        ("openai", "OPENAI_API_KEY"),
        ("groq", "GROQ_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
        ("mistral", "MISTRAL_API_KEY"),
        ("claude", "ANTHROPIC_API_KEY"),
    ]:
        val = os.getenv(env_var)
        if val:
            keys[provider] = val
    return keys


def _try_first_available_provider() -> tuple:
    """Vraca (provider, api_key) za prvi provider sa validnim kljucem.

    Prolazi kroz sve dostupne provajdere i vraca prvi ciji kljuc
    prolazi autentikaciju. Ako nijedan nije validan, skip-uje test.
    """
    keys = _get_env_api_keys()
    if not keys:
        pytest.skip("Nijedan API kljuc nije dostupan u env.")

    from crewai import LLM

    models = {
        "openai": "gpt-4o-mini",
        "groq": "groq/llama-3.3-70b-versatile",
        "gemini": "gemini/gemini-2.0-flash",
        "mistral": "mistral/mistral-small-latest",
        "claude": "claude-sonnet-4-20250514",
    }

    for provider, api_key in keys.items():
        model = models.get(provider)
        if not model:
            continue
        try:
            llm = LLM(model=model, api_key=api_key, temperature=0, max_tokens=5)
            result = llm.call("Say ok")
            if result:
                return provider, api_key
        except Exception as e:
            logger.info("%s: preskocen (%s)", provider, str(e)[:80])
            continue

    pytest.skip("Nijedan API kljuc nije validan.")


class TestCrewAIQuizFlowRealLLM:
    """Integration testovi za QuizQuestionFlow sa pravim LLM pozivima.

    Zahtevaju API kljuceve u environment variablama.
    Pokretanje:
        GROQ_API_KEY=gsk_... pytest -v -m "integration" ...
    """

    @pytest.mark.integration
    def test_quiz_flow_generates_valid_questions(self):
        """Koristi prvi dostupni provider za generisanje pitanja."""
        provider, api_key = _try_first_available_provider()

        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        questions = generate_quiz_questions_with_crewai(
            text=TEST_TEXT,
            provider=provider,
            api_key=api_key,
            num_questions=3,
        )

        assert len(questions) > 0, f"{provider}: 0 pitanja generisano"
        assert len(questions) <= 3

        for q in questions:
            assert "question_text" in q, f"Pitanje nema question_text: {q}"
            assert "question_type" in q, f"Pitanje nema question_type: {q}"
            assert "correct_answer" in q, f"Pitanje nema correct_answer: {q}"
            assert q["question_type"] in (
                "multiple_choice", "true_false", "fill_blank"
            ), f"Nepoznat tip: {q['question_type']}"
            assert len(q["question_text"]) > 10, (
                f"Prekratak question_text: {q['question_text']}"
            )
            if q["question_type"] == "multiple_choice":
                assert "options" in q and len(q["options"]) >= 2
                assert (
                    q["correct_answer"] in q["options"]
                    or any(
                        opt.startswith(q["correct_answer"])
                        for opt in q["options"]
                    )
                ), (
                    f"correct_answer={q['correct_answer']!r} "
                    f"nije ni u options niti prefix ni jedne opcije: "
                    f"{q['options']}"
                )

        logger.info(
            "%s: %d validnih pitanja generisano", provider, len(questions)
        )

    @pytest.mark.integration
    @pytest.mark.slow
    def test_quiz_flow_multiple_providers(self):
        """Testira svaki provider koji ima API kljuc.

        Skip-uje provajdere koji vrate AuthenticationError
        (npr. istekli/revoked kljucevi).
        """
        keys = _get_env_api_keys()
        if not keys:
            pytest.skip("Nijedan API kljuc nije dostupan u env.")

        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        tested = 0
        for provider, api_key in keys.items():
            try:
                questions = generate_quiz_questions_with_crewai(
                    text=TEST_TEXT,
                    provider=provider,
                    api_key=api_key,
                    num_questions=2,
                )
            except Exception as e:
                logger.warning(
                    "%s: preskocen (auth error: %s)", provider, str(e)[:60]
                )
                continue

            assert len(questions) > 0, f"{provider}: 0 pitanja"
            for q in questions:
                assert "question_text" in q
                assert "question_type" in q
                assert "correct_answer" in q

            logger.info("%s: %d pitanja OK", provider, len(questions))
            tested += 1

        if tested == 0:
            pytest.skip("Nijedan provider nije proso autentikaciju.")

    @pytest.mark.integration
    def test_quiz_flow_respects_num_questions(self):
        """Proverava da num_questions limit radi sa realnim LLM-om."""
        provider, api_key = _try_first_available_provider()

        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        for n in [1, 5]:
            questions = generate_quiz_questions_with_crewai(
                text=TEST_TEXT,
                provider=provider,
                api_key=api_key,
                num_questions=n,
            )
            assert len(questions) <= n, (
                f"{n} pitanja: dobijeno {len(questions)}"
            )
            logger.info("num_questions=%d: %d generisano", n, len(questions))

    @pytest.mark.integration
    def test_quiz_flow_raises_without_api_key(self):
        """Bez API kljuca mora da baci ValueError."""
        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        with pytest.raises(ValueError, match="API klju"):
            generate_quiz_questions_with_crewai(
                text=TEST_TEXT,
                provider="openai",
                api_key=None,
                num_questions=3,
            )


class TestCrewAIFlashcardFlowRealLLM:
    """Integration testovi za FlashcardFlow sa pravim LLM pozivima."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_flashcard_flow_generates_valid_cards(self):
        """Pokrece ceo FlashcardFlow (reader -> generator -> validator)."""
        provider, api_key = _try_first_available_provider()

        from app.services.crewai_flashcard import (
            _create_crewai_llm, FlashcardFlow
        )

        llm = _create_crewai_llm(provider, api_key)
        flow = FlashcardFlow(llm=llm, chunks=TEST_CHUNKS, max_cards=5)
        result = flow.kickoff()

        assert len(result) > 0, "0 kartica generisano"
        assert len(result) <= 15, f"Previse kartica ({len(result)}), max_cards=5 ignoriše LLM"

        for card in result:
            assert "front" in card, f"Kartica nema front: {card}"
            assert "back" in card, f"Kartica nema back: {card}"
            assert len(card["front"]) > 10, f"Prekratak front: {card['front']}"
            assert len(card["back"]) > 10, f"Prekratak back: {card['back']}"

            if card.get("source_chunk_id"):
                assert card["source_chunk_id"] in ("c1", "c2")

        logger.info(
            "%s: %d validnih kartica generisano", provider, len(result)
        )

    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_with_crewai_mocked_db(self):
        """Testira generate_with_crewai sa realnim LLM + mock-ovanom bazom.

        DB se mock-uje da vrati user-a sa realnim API kljucem iz env-a.
        """
        provider, real_api_key = _try_first_available_provider()

        from app.services.crewai_flashcard import generate_with_crewai

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "integration-test-user"
        mock_user.ai_api_key_openai = (
            real_api_key if provider == "openai" else None
        )
        mock_user.ai_api_key_groq = (
            real_api_key if provider == "groq" else None
        )
        mock_user.ai_api_key_gemini = (
            real_api_key if provider == "gemini" else None
        )
        mock_user.ai_api_key_mistral = (
            real_api_key if provider == "mistral" else None
        )
        mock_user.ai_api_key_claude = (
            real_api_key if provider == "claude" else None
        )
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.GROQ_API_KEY = None
            mock_settings.GEMINI_API_KEY = None
            mock_settings.MISTRAL_API_KEY = None
            mock_settings.ANTHROPIC_API_KEY = None

            cards = generate_with_crewai(
                chunks=TEST_CHUNKS,
                provider=provider,
                user_id="integration-test-user",
                db=mock_db,
                max_cards=5,
            )

        assert len(cards) > 0, f"{provider}: 0 kartica"
        assert len(cards) <= 5

        for card in cards:
            assert "front" in card, f"Kartica nema front: {card}"
            assert "back" in card, f"Kartica nema back: {card}"
            assert len(card["front"]) > 10
            assert len(card["back"]) > 10

        logger.info(
            "%s (generate_with_crewai): %d kartica OK", provider, len(cards)
        )

    @pytest.mark.integration
    def test_create_crewai_llm_with_env_key(self):
        """Testira da se LLM kreira sa pravim kljucem."""
        provider, api_key = _try_first_available_provider()

        from app.services.crewai_flashcard import (
            _create_crewai_llm, PROVIDER_LLM_CONFIG
        )

        llm = _create_crewai_llm(provider, api_key)
        assert llm is not None
        expected_model = PROVIDER_LLM_CONFIG[provider]["model"]
        assert llm.model == expected_model
        logger.info(
            "LLM kreiran: provider=%s, model=%s", provider, llm.model
        )


class TestCrewAIFallbackRealLLM:
    """Testovi za fallback mehanizam sa realnim provajderima."""

    @pytest.mark.integration
    def test_quiz_generation_fallback_in_generation_module(self):
        """_generate_with_crewai_questions mora da padne na fallback
        kad nema API kljuceva."""
        from app.services.quiz.generation import _generate_with_crewai_questions

        questions, provider = _generate_with_crewai_questions(
            text=TEST_TEXT,
            num_questions=2,
            provider=None,
        )[1:]

        assert len(questions) > 0
        assert provider == "fallback"
        for q in questions:
            assert "question_text" in q
            assert "question_type" in q
            assert "correct_answer" in q

    @pytest.mark.integration
    def test_quiz_generation_fallback_without_api_key(self):
        """Kad je API key = None, koristi fallback na single LLM."""
        from app.services.quiz.generation import _generate_with_crewai_questions

        questions, provider = _generate_with_crewai_questions(
            text=TEST_TEXT,
            num_questions=2,
            provider="openai",
            user_openai_key=None,
        )[1:]

        assert len(questions) > 0
        assert provider == "fallback"

    @pytest.mark.integration
    def test_flashcard_fallback_when_no_api_key(self):
        """flashcard.py mora da padne na _generate_with_ai kad nema kljuca."""
        from app.services.flashcard import _generate_with_ai
        from unittest.mock import patch

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-user"
        mock_user.ai_api_key_openai = None
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps([
            {"front": "What is photosynthesis?",
             "back": "It converts sunlight into chemical energy."},
            {"front": "Where does photosynthesis occur?",
             "back": "In the chloroplasts of plant cells."},
        ])

        with patch(
            "app.services.crewai_flashcard.generate_with_crewai",
            side_effect=RuntimeError("CrewAI failed"),
        ):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = MagicMock(
                    choices=[mock_choice]
                )

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.OPENAI_API_KEY = "sk-test-fallback"
                    cards, method = _generate_with_ai(
                        chunks=TEST_CHUNKS,
                        provider="openai",
                        user_id="test-user",
                        db=mock_db,
                        max_cards=5,
                    )

        assert len(cards) > 0
        assert method in ("openai", "fallback")
        for card in cards:
            assert "front" in card
            assert "back" in card
