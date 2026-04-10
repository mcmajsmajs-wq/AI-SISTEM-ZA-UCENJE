# Import all models to ensure proper loading order for SQLAlchemy relationships
from app.db.models.user import User, UserSession  # noqa: F401
from app.db.models.document import Document, Chunk  # noqa: F401
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer, QuizImage  # noqa: F401
from app.db.models.file import File  # noqa: F401
from app.db.models.conversation import Conversation, Message  # noqa: F401
from app.db.models.study_plan import StudyPlan, StudyPlanItem  # noqa: F401
