"""Add L0/L1/L2 tiered loading tables with pgvector

Creates 3 tiered knowledge tables:
- L0: knowledge_document_summaries — document-level summary + embedding
- L1: knowledge_section_summaries — section-level summary + embedding
- L2: knowledge_chunks — individual chunks + embedding

Revision ID: 012
Revises: 011
Create Date: 2026-06-02 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Enable pgvector extension
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # 2. Create knowledge_chunks (L2) with embedding
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding vector(384),
            chunk_index INTEGER NOT NULL,
            section_index INTEGER,
            section_title VARCHAR(500),
            heading_level INTEGER,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    )
    conn.execute(
        sa.text(
            "ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS embedding vector(384)"
        )
    )

    # 3. Create knowledge_section_summaries (L1) with embedding
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS knowledge_section_summaries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
            section_index INTEGER NOT NULL,
            section_title VARCHAR(500),
            heading_level INTEGER DEFAULT 1,
            content TEXT,
            summary TEXT,
            embedding vector(384),
            chunk_count INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    )
    conn.execute(
        sa.text(
            "ALTER TABLE knowledge_section_summaries ADD COLUMN IF NOT EXISTS embedding vector(384)"
        )
    )

    # 4. Create knowledge_document_summaries (L0) with embedding
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS knowledge_document_summaries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
            document_title VARCHAR(500),
            summary TEXT,
            embedding vector(384),
            chunk_count INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    )
    conn.execute(
        sa.text(
            "ALTER TABLE knowledge_document_summaries ADD COLUMN IF NOT EXISTS embedding vector(384)"
        )
    )

    # 5. Create indexes
    # knowledge_chunks indexes
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding
        ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)
    )
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_source_id
        ON knowledge_chunks (source_id)
    """)
    )
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_section
        ON knowledge_chunks (source_id, section_index)
    """)
    )

    # knowledge_section_summaries indexes
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_section_summaries_embedding
        ON knowledge_section_summaries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)
    )
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_section_summaries_source
        ON knowledge_section_summaries (source_id)
    """)
    )
    conn.execute(
        sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_section_summaries_section
        ON knowledge_section_summaries (source_id, section_index)
    """)
    )

    # knowledge_document_summaries indexes
    conn.execute(
        sa.text("""
        CREATE INDEX IF NOT EXISTS ix_document_summaries_embedding
        ON knowledge_document_summaries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)
    )
    conn.execute(
        sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_document_summaries_source
        ON knowledge_document_summaries (source_id)
    """)
    )


def downgrade():
    conn = op.get_bind()

    # Drop indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_document_summaries_source"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_document_summaries_embedding"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_section_summaries_section"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_section_summaries_source"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_section_summaries_embedding"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_knowledge_chunks_section"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_knowledge_chunks_source_id"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding"))

    # Drop tables (CASCADE handles dependent objects)
    conn.execute(sa.text("DROP TABLE IF EXISTS knowledge_document_summaries CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS knowledge_section_summaries CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS knowledge_chunks CASCADE"))

    # Note: vector extension intentionally NOT dropped
    # (may be used by other features in the future)
