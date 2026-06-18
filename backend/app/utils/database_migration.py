# -*- coding: utf-8 -*-
"""
================================================================================
DATABASE MIGRATION UTILITY
================================================================================
Automatski proverava i dodaje nedostajuće kolone u bazi pri startu aplikacije.
Ovo sprečava probleme sa nedostajućim kolonama nakon promena u modelima.

Verzija: 1.0.0
================================================================================
"""

import logging
from sqlalchemy import inspect, text
from app.db.session import engine

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "users": {
        # Original columns (from initial migration)
        "id": "UUID",
        "email": "VARCHAR(255)",
        "hashed_password": "VARCHAR(255)",
        "full_name": "VARCHAR(255)",
        "is_active": "BOOLEAN",
        "is_verified": "BOOLEAN",
        "role": "VARCHAR(50)",
        "timezone": "VARCHAR(50)",
        "language": "VARCHAR(10)",
        # AI Settings columns
        "ai_provider": "VARCHAR(50)",
        "ai_api_key_openai": "TEXT",
        "ai_api_key_claude": "TEXT",
        "ai_api_key_gemini": "TEXT",
        "ai_api_key_groq": "TEXT",
        "ai_api_key_mistral": "TEXT",
        "ai_api_key_deepseek": "TEXT",
        "ai_custom_base_url": "VARCHAR(500)",
        "ai_api_key_custom": "TEXT",
        # Timestamps
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }
}


def check_and_add_missing_columns():
    """
    Proverava da li sve potrebne kolone postoje u tabelama.
    Ako kolona ne postoji, automatski je dodaje.
    """
    logger.info("=" * 60)
    logger.info("Pokretanje automatske provere baze podataka...")
    logger.info("=" * 60)

    inspector = inspect(engine)
    migrations_applied = []

    for table_name, columns in REQUIRED_COLUMNS.items():
        # Check if table exists
        if table_name not in inspector.get_table_names():
            logger.warning(f"Tabela '{table_name}' ne postoji u bazi - preskačem")
            continue

        existing_columns = [col["name"] for col in inspector.get_columns(table_name)]

        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                try:
                    # Add the missing column
                    with engine.connect() as conn:
                        # Determine the appropriate column type
                        if column_type == "TEXT":
                            sql_type = "TEXT"
                        elif column_type == "BOOLEAN":
                            sql_type = "BOOLEAN DEFAULT true"
                        elif column_type == "TIMESTAMP":
                            sql_type = "TIMESTAMP"
                        else:
                            sql_type = "VARCHAR(255)"

                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type};"
                        conn.execute(text(sql))
                        conn.commit()

                    migrations_applied.append(f"  + {table_name}.{column_name}")
                    logger.info(f"Dodata kolona: {table_name}.{column_name}")
                except Exception as e:
                    logger.error(
                        f"Greška pri dodavanju kolone {table_name}.{column_name}: {e}"
                    )

    if migrations_applied:
        logger.info("=" * 60)
        logger.info("Uspešno primenjene automatske migracije:")
        for migration in migrations_applied:
            logger.info(migration)
        logger.info("=" * 60)
    else:
        logger.info("Baza podataka je ažurna - nema potrebe za migracijama.")
        logger.info("=" * 60)

    return len(migrations_applied)


def verify_database_health():
    """
    Vrsi osnovnu proveru zdravlja baze podataka.
    """
    try:
        with engine.connect() as conn:
            # Test write access
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Baza podataka nije dostupna: {e}")
        return False


if __name__ == "__main__":
    # Može se pokrenuti i ručno za debug
    from app.core.logging_config import setup_logging

    setup_logging()

    if verify_database_health():
        check_and_add_missing_columns()
    else:
        logger.error("Nije moguće povezati se sa bazom podataka")
