"""Create flashcard tables (Deck, Flashcard, ReviewLog)

Revision ID: 015
Revises: 014
Create Date: 2026-07-03

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_decks_user_id"), "decks", ["user_id"])

    op.create_table(
        "flashcards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("deck_id", UUID(as_uuid=True), sa.ForeignKey("decks.id"), nullable=False, index=True),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("source_chunk_id", UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_flashcards_deck_id"), "flashcards", ["deck_id"])

    op.create_table(
        "review_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("flashcards.id"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("ease_factor", sa.Float(), server_default="2.5"),
        sa.Column("interval", sa.Integer(), server_default="0"),
        sa.Column("repetitions", sa.Integer(), server_default="0"),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_review_logs_card_id"), "review_logs", ["card_id"])
    op.create_index(op.f("ix_review_logs_user_id"), "review_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("review_logs")
    op.drop_table("flashcards")
    op.drop_table("decks")
