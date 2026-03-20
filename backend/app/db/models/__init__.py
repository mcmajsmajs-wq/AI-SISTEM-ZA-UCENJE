# Import all models to ensure proper loading order for SQLAlchemy relationships
from app.db.models.user import User, UserSession
from app.db.models.document import Document, Chunk
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer, QuizImage
from app.db.models.file import File
from app.db.models.conversation import Conversation, Message
from app.db.models.study_plan import StudyPlan, StudyPlanItem
