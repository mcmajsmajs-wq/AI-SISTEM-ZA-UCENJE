import json
import logging
from typing import List, Optional

from crewai import Agent, Task, Crew, LLM
from crewai.flow import Flow, start, listen

from app.services.quiz.helpers.parsing import _validate_questions

logger = logging.getLogger(__name__)

PROVIDER_LLM_CONFIG = {
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": None,
    },
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
    },
    "gemini": {
        "model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "mistral": {
        "model": "mistral-small-latest",
        "base_url": "https://api.mistral.ai/v1",
    },
    "claude": {
        "model": "claude-sonnet-4-20250514",
        "base_url": None,
    },
}


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("["):
        close = text.rfind("]")
        if close != -1:
            text = text[:close + 1]
    elif text.startswith("{"):
        close = text.rfind("}")
        if close != -1:
            text = text[:close + 1]
    return text.strip()


def _create_crewai_llm(provider: str, api_key: str) -> LLM:
    cfg = PROVIDER_LLM_CONFIG.get(provider)
    if not cfg:
        raise ValueError(f"Nepodržan provajder za CrewAI: {provider}")

    if provider == "claude":
        return LLM(model=cfg["model"], api_key=api_key)

    kwargs = {"model": cfg["model"], "api_key": api_key}
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]
    return LLM(**kwargs)


def _run_crew(agent: Agent, task: Task) -> str:
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return crew.kickoff().raw


def _get_combined_text(
    chunks: List, max_chunks: int = 10, max_chars: int = 400
) -> str:
    texts = []
    total = 0
    for c in chunks[:max_chunks]:
        if c.content:
            snippet = c.content[:max_chars]
            texts.append(snippet)
            total += len(snippet)
    result = "\n\n---\n\n".join(texts)
    return result[:5000]


def _detect_language(text: str) -> str:
    """Detect if text is predominantly Serbian/Croatian or English."""
    sr_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    total = len(text)
    if total > 0 and sr_chars / total > 0.05:
        return "srpski"
    return "english"


def _lang_instruction(text: str) -> str:
    lang = _detect_language(text)
    if lang == "srpski":
        return (
            "JEZIK: OBAVEZNO odgovaraj samo na srpskom jeziku. "
            "NIKAKO ne koristi engleski. "
            "KORISTI isključivo LATINICU (ne ćirilicu). "
            "Svi koncepti, pitanja, odgovori i objašnjenja moraju biti na srpskom latinici."
        )
    return ""


def _prepend_lang(description: str, text: str) -> str:
    instr = _lang_instruction(text)
    if instr:
        return instr + "\n\n" + description
    return description


def _run_content_reader(llm: LLM, text: str) -> str:
    lang = _detect_language(text)
    agent = Agent(
        role="Content Reader",
        goal=(
            "Read the following text chunks and identify the main concepts, "
            "key terms, and important facts. Return a structured summary "
            "with each concept and its context."
        ),
        backstory=(
            "You are an expert at analyzing educational text and extracting "
            "structured information for study material creation."
        ),
        llm=llm,
        verbose=False,
    )
    task = Task(
        description=_prepend_lang(
            "Extract the main concepts, key terms, and important facts "
            "from the text below. Organize them as a structured summary "
            "with each concept explained in its context.\n\n"
            f"Text:\n{text}",
            text
        ),
        expected_output=(
            "A structured summary of concepts, key terms, and important "
            "facts with their context."
        ),
        agent=agent,
    )
    return _run_crew(agent, task)


class FlashcardFlow(Flow):
    def __init__(self, llm: LLM, chunks: List, max_cards: int = 20):
        super().__init__()
        self.llm = llm
        self.chunks = chunks
        self.max_cards = max_cards
        self._generated_summary = ""

    def _combined_text(self) -> str:
        return _get_combined_text(self.chunks)

    def _lang_instruction(self) -> str:
        text = self._combined_text()
        return _lang_instruction(text)

    def _make_crew(self, agent: Agent, task: Task) -> str:
        return _run_crew(agent, task)

    @start()
    def read_content(self) -> str:
        return _run_content_reader(self.llm, self._combined_text())

    @listen(read_content)
    def generate_cards(self, summary: str) -> str:
        self._generated_summary = summary
        return self._run_generator(summary)

    def _run_generator(self, summary: str, feedback: str = "") -> str:
        agent = Agent(
            role="Flashcard Generator",
            goal=(
                "Create up to {max_cards} flashcards directly about the "
                "content below. Every card MUST be about the subject "
                "matter in the text (e.g. VMware, Podman, hemija, etc.), "
                "NOT about flashcards or the flashcard-generating process. "
                "Each flashcard must have a 'front' (question/term - "
                "complete sentence) and 'back' (answer/definition). "
                "Return as JSON array.".format(max_cards=self.max_cards)
            ),
            backstory=(
                "You are an expert educator who creates clear, concise, "
                "and effective flashcards for study purposes."
            ),
            llm=self.llm,
            verbose=False,
        )

        instr = self._lang_instruction()
        desc = (
            f"{instr}\n\n" if instr else ""
            f"Based on the following summary of the document content, "
            f"create up to {self.max_cards} flashcards.\n\n"
            f"CRITICAL: The flashcards must be about the DOCUMENT CONTENT "
            f"(e.g. VMware, Podman, chemistry, biology), NOT about "
            f"flashcards or the flashcard generation process. "
            f"Never say 'flashcard' in the front or back text.\n\n"
            f"Each flashcard must have:\n"
            f"- 'front': a question or term from the content\n"
            f"- 'back': the answer or definition\n\n"
            f"Return ONLY a valid JSON array of objects with 'front' and "
            f"'back' fields.\n\n"
            f"Example for a biology document:\n"
            f'[{{"front": "Šta je fotosinteza?", '
            f'"back": "Fotosinteza je proces kojim biljke pretvaraju '
            f'svetlosnu energiju u hemijsku."}}]\n\n'
            f"Summary:\n{summary}"
        )
        if feedback:
            desc += f"\n\nThe previous validation had the following issues. Please fix them:\n{feedback}"

        task = Task(
            description=desc,
            expected_output=(
                "A JSON array of flashcard objects with 'front' and 'back' fields."
            ),
            agent=agent,
        )
        return self._make_crew(agent, task)

    @listen(generate_cards)
    def validate_cards(self, cards_raw: str) -> list:
        result = self._run_validator(cards_raw)
        try:
            val_data = json.loads(_clean_json(result))
        except json.JSONDecodeError:
            logger.warning(
                "CrewAI validator: JSON parse error, "
                "using raw generator output"
            )
            try:
                return json.loads(_clean_json(cards_raw))
            except json.JSONDecodeError:
                raise ValueError(
                    "CrewAI: ni validacija ni generacija "
                    "nisu vratili validan JSON."
                )

        retried = getattr(self, "_retried", False)
        invalid_pct = val_data.get("invalid_count", 0) / max(val_data.get("total_count", 1), 1)
        if invalid_pct > 0.75 and not retried:
            logger.info("CrewAI validation: >75%% invalid, retrying generation once")
            self._retried = True
            feedback = val_data.get("feedback", "")
            new_raw = self._run_generator(self._generated_summary, feedback)
            result = self._run_validator(new_raw)
            val_data = json.loads(_clean_json(result))

        cards = val_data.get("valid_cards", val_data.get("output", []))
        if not cards:
            raise ValueError("CrewAI produkovao 0 validnih kartica.")

        return cards

    def _run_validator(self, cards_raw: str) -> str:
        agent = Agent(
            role="Validator",
            goal=(
                "Validate these flashcards against the original text. Check: "
                "(1) Each front is a meaningful term or question, "
                "(2) Each back provides useful context or answer, "
                "(3) No duplicates, "
                "(4) No metadata/navigation text. "
                "Be lenient - most generated cards should pass. "
                "Only reject truly bad cards (empty, gibberish, metadata). "
                "Return all cards as valid unless clearly unusable."
            ),
            backstory=(
                "You are a quality assurance expert for educational content. "
                "You catch truly bad cards but accept reasonable ones."
            ),
            llm=self.llm,
            verbose=False,
        )
        instr = self._lang_instruction()
        task = Task(
            description=_prepend_lang(
                "Validate these flashcards against the original text.\n\n"
                "Rules:\n"
                "1. Each front should be a meaningful term or question\n"
                "2. Each back should provide useful context\n"
                "3. Reject only: empty cards, gibberish, or obvious metadata text\n"
                "4. Be LENIENT - most cards should pass validation\n\n"
                f"Original text:\n{self._combined_text()[:2000]}\n\n"
                f"Flashcards to validate:\n{cards_raw}\n\n"
                "Return ONLY a valid JSON object with this structure:\n"
                '{{\n'
                '  "valid_cards": [list of valid {{"front": "...", "back": "..."}} objects],\n'
                '  "invalid_count": number of invalid cards,\n'
                '  "total_count": total number of cards,\n'
                '  "requires_retry": true (if >75% invalid) or false,\n'
                '  "feedback": "brief explanation of issues found"\n'
                "}}",
                self._combined_text()
            ),
            expected_output=(
                "A JSON object with validated cards, counts, and retry decision."
            ),
            agent=agent,
        )
        return self._make_crew(agent, task)


class QuizQuestionFlow(Flow):
    def __init__(self, llm: LLM, text: str, num_questions: int = 5):
        super().__init__()
        self.llm = llm
        self.text = text
        self.num_questions = num_questions

    @start()
    def read_content(self) -> str:
        return _run_content_reader(self.llm, self.text)

    @listen(read_content)
    def generate_questions(self, summary: str) -> str:
        agent = Agent(
            role="Question Generator",
            goal=(
                "Based on the following concepts and context, generate up to "
                f"{self.num_questions} quiz questions. Each question must have: "
                "question_text, question_type (multiple_choice, true_false, or "
                "fill_blank), options (for multiple_choice), correct_answer, "
                "and explanation. Return as JSON array."
            ),
            backstory=(
                "You are an expert educator who creates clear, pedagogically "
                "sound quiz questions for assessment purposes."
            ),
            llm=self.llm,
            verbose=False,
        )

        t = self.text
        lang_hint = _lang_instruction(t)

        lines = [
            f"{lang_hint}\n\n" if lang_hint else "",
            f"Based on the following concepts and context, generate up to "
            f"{self.num_questions} quiz questions.\n\n"
            f"Each question must have:\n"
            f"- question_text: the question text\n"
            f"- question_type: one of multiple_choice, true_false, or fill_blank\n"
            f"- options: array of answer choices (required for multiple_choice)\n"
            f"- correct_answer: the correct answer (must match one of the options "
            f"for multiple_choice and true_false)\n"
            f"- explanation: brief explanation of the correct answer\n\n"
            f"For true_false questions, options must be ['True', 'False'] "
            f"and correct_answer must be 'True' or 'False'.\n\n"
            f"For fill_blank questions, the question_text should contain a "
            f"blank (e.g. 'The capital of France is ___') and correct_answer "
            f"should be the answer.\n\n"
            f"Return ONLY a valid JSON array of question objects.\n\n",
            "Example:\n[\n"
            '  {"question_text": "What is photosynthesis?",\n'
            '   "question_type": "multiple_choice",\n'
   '   "options": ["A) Process by which plants convert sunlight into energy", '
             '"B) Process by which animals breathe", '
             '"C) Process of water evaporation", '
             '"D) Process of soil formation"],\n'
             '   "correct_answer": "A",\n'
             '   "explanation": "Photosynthesis converts light into chemical energy."\n'
            "  },\n"
            '  {"question_type": "true_false",\n'
            '   "question_text": "Is photosynthesis a process in plants?",\n'
            '   "options": ["True", "False"],\n'
            '   "correct_answer": "True",\n'
            '   "explanation": "Photosynthesis occurs only in plants."\n'
            "  }\n"
            "]\n\n",
             f"Summary:\n{summary}",
             lang_hint,
        ]
        desc = "".join(lines)

        task = Task(
            description=desc,
            expected_output=(
                "A JSON array of question objects with question_text, "
                "question_type, options, correct_answer, and explanation."
            ),
            agent=agent,
        )
        return _run_crew(agent, task)

    @listen(generate_questions)
    def validate_questions(self, questions_raw: str) -> list:
        cleaned = _clean_json(questions_raw)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("CrewAI quiz: failed to parse JSON, trying fallback parse")
            parsed = []

        if isinstance(parsed, list):
            questions = _validate_questions(parsed)
        elif isinstance(parsed, dict):
            questions = _validate_questions([parsed])
        else:
            questions = []

        if not questions:
            logger.warning("CrewAI quiz: 0 valid questions generated")
            return []

        return questions[:self.num_questions]


def generate_quiz_questions_with_crewai(
    text: str,
    provider: str,
    api_key: Optional[str] = None,
    num_questions: int = 5,
) -> list:
    if not api_key:
        raise ValueError(f"{provider.capitalize()} API ključ nije podešen za CrewAI.")

    llm = _create_crewai_llm(provider, api_key)
    flow = QuizQuestionFlow(llm=llm, text=text, num_questions=num_questions)
    return flow.kickoff()[:num_questions]


def generate_with_crewai(
    chunks: List,
    provider: str,
    user_id,
    db,
    max_cards: int = 20,
) -> list:
    from app.core.config import settings
    from app.db.models.user import User

    cfg = PROVIDER_LLM_CONFIG.get(provider)
    if not cfg:
        raise ValueError(f"Nepodržan provajder za CrewAI: {provider}")

    user = db.query(User).filter(User.id == user_id).first() if user_id else None

    if provider == "claude":
        api_key = (
            (user.ai_api_key_claude if user else None)
            or settings.ANTHROPIC_API_KEY
        )
    else:
        key_source = {
            "openai": lambda u, s: (
                (u.ai_api_key_openai if u else None) or s.OPENAI_API_KEY
            ),
            "groq": lambda u, s: (
                (u.ai_api_key_groq if u else None) or s.GROQ_API_KEY
            ),
            "gemini": lambda u, s: (
                (u.ai_api_key_gemini if u else None) or s.GEMINI_API_KEY
            ),
            "mistral": lambda u, s: (
                (u.ai_api_key_mistral if u else None) or s.MISTRAL_API_KEY
            ),
        }.get(provider)
        api_key = key_source(user, settings) if key_source else None

    if not api_key:
        raise ValueError(f"{provider.capitalize()} API ključ nije podešen za CrewAI.")

    llm = _create_crewai_llm(provider, api_key)
    flow = FlashcardFlow(llm=llm, chunks=chunks, max_cards=max_cards)
    result = flow.kickoff()

    validated = []
    for card in result:
        validated.append({
            "front": (card.get("front") or "")[:500],
            "back": (card.get("back") or "")[:1000],
            "source_chunk_id": None,
        })

    return validated[:max_cards]
