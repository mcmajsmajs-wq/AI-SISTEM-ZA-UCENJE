from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User gamification columns
    op.add_column("users", sa.Column("xp", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("level", sa.Integer(), server_default="1", nullable=False))
    op.add_column("users", sa.Column("total_xp_earned", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("last_activity_date", sa.DateTime(timezone=True), nullable=True))

    # Badges table
    op.create_table(
        "badges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon_name", sa.String(100), server_default="trophy", nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default="0"),
        sa.Column("criteria_type", sa.String(100), nullable=False),
        sa.Column("criteria_threshold", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_badges_slug"), "badges", ["slug"])

    # User badges table
    op.create_table(
        "user_badges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("badge_id", UUID(as_uuid=True), sa.ForeignKey("badges.id"), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_user_badges_user_id"), "user_badges", ["user_id"])

    # Seed badge catalog
    op.execute(
        """
        INSERT INTO badges (id, slug, name, description, icon_name, xp_reward, criteria_type, criteria_threshold) VALUES
        (gen_random_uuid(), 'first_quiz', 'Prvi korak', 'Reši svoj prvi kviz', 'trophy', 25, 'quizzes_completed', 1),
        (gen_random_uuid(), 'quiz_master', 'Majstor kvizova', 'Reši 10 kvizova', 'zap', 100, 'quizzes_completed', 10),
        (gen_random_uuid(), 'perfect_score', 'Savršenstvo', 'Ostvari 100% na kvizu', 'star', 75, 'perfect_score', 1),
        (gen_random_uuid(), 'streak_7', 'Nedeljni heroj', 'Ostvari 7-dnevni streak', 'flame', 50, 'streak_days', 7),
        (gen_random_uuid(), 'streak_30', 'Mesečni šampion', 'Ostvari 30-dnevni streak', 'flame', 200, 'streak_days', 30),
        (gen_random_uuid(), 'document_processor', 'Obrađivač', 'Obradi 5 dokumenata', 'file-text', 50, 'documents_processed', 5),
        (gen_random_uuid(), 'ten_quizzes_pass', 'Serijski rešavač', 'Položi 10 kvizova zaredom', 'zap', 150, 'consecutive_passes', 10),
        (gen_random_uuid(), 'knowledge_seeker', 'Tragač znanja', 'Pošalji 25 upita u bazu znanja', 'search', 100, 'knowledge_queries', 25)
        """
    )


def downgrade() -> None:
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_column("users", "xp")
    op.drop_column("users", "level")
    op.drop_column("users", "total_xp_earned")
    op.drop_column("users", "current_streak")
    op.drop_column("users", "longest_streak")
    op.drop_column("users", "last_activity_date")
