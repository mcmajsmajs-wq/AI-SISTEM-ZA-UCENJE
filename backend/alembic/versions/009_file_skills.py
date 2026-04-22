"""
File Skills - Skills za obradu fajlova (translate, pdf, docx, xlsx)

Verzija: 1.0.0 (FAZA 13 - File Skills)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "009_file_skills"
down_revision = "008_question_used"
branch_labels = None
depends_on = None


def upgrade():
    # Kreiraj file_skills tabelu
    op.create_table(
        "file_skills",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )

    # Seed data - translate skill
    op.execute("""
        INSERT INTO file_skills (id, name, category, description, prompt_template, is_active)
        VALUES (
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            'translate',
            'translate',
            'Lep formatiran prevod sa poglavljima i strukturiranim tekstom',
            'You are a professional translator. Translate the text to target language with:
1. Preserve all chapters and sections as headings
2. Keep numbering of lists and items
3. Use markdown formatting for emphasis
4. Translate each chunk independently but maintain consistency
5. Output ONLY the translated text, no explanations',
            true
        )
    """)

    # Seed data - pdf skill
    op.execute("""
        INSERT INTO file_skills (id, name, category, description, prompt_template, is_active)
        VALUES (
            'b2c3d4e5-f6a7-8901-bcde-f12345678901',
            'pdf',
            'pdf',
            'Lep PDF dokument sa header/footer i numerisanim stranama',
            'Create a professional PDF document with:
1. Add header with document title
2. Add page numbers at bottom
3. Use proper margins (2cm)
4. Bold section headings
5. Justified text
6. Include table of contents if possible
7. Professional font (DejaVuSans or Helvetica)',
            true
        )
    """)

    # Seed data - docx skill
    op.execute("""
        INSERT INTO file_skills (id, name, category, description, prompt_template, is_active)
        VALUES (
            'c3d4e5f6-a7b8-9012-cdef-123456789012',
            'docx',
            'docx',
            'Lep Word dokument sa stilovima i TOC',
            'Create a professional Word document with:
1. Use heading styles for sections
2. Add page numbers
3. Create table of contents
4. Use bullet points for lists
5. Bold for important terms
6. Professional formatting
7. Include title page if appropriate',
            true
        )
    """)


def downgrade():
    op.drop_table("file_skills")
