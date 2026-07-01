# Import all models to ensure proper loading order for SQLAlchemy relationships
from app.db.models.user import User, UserSession  # noqa: F401
from app.db.models.document import Document, Chunk  # noqa: F401
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer, QuizImage  # noqa: F401
from app.db.models.file import File  # noqa: F401
from app.db.models.conversation import Conversation, Message  # noqa: F401
from app.db.models.study_plan import StudyPlan, StudyPlanItem  # noqa: F401

# Import Skill model to ensure it's registered before User relationship is established
try:
    from app.services.skills.models import Skill, SkillTemplate, DocumentType  # noqa: F401
except ImportError:
    pass  # Skills module not available

# Knowledge / RAG models
from app.db.models.knowledge import (  # noqa: F401
    KnowledgeSource,
    KnowledgeChunk,
    KnowledgeSectionSummary,
    KnowledgeDocumentSummary,
)
from app.db.models.gamification import Badge, UserBadge  # noqa: F401
