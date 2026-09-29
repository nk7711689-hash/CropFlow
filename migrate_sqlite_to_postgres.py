"""Copy the existing SQLite data into the configured PostgreSQL database."""

from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, text

from app import app, db, initialize_database
from models import Product, ProductImage, Reservation, User, Message, MessagePermission, Worker


ROOT = Path(__file__).resolve().parent
SQLITE_PATH = ROOT / "instance" / "cropflow.db"
TABLES = (User, Product, ProductImage, Reservation, Message, MessagePermission, Worker)


def read_source_rows(source_engine, model):
    """Read only columns that exist in both SQLite and the SQLAlchemy model."""
    source_columns = {column["name"] for column in inspect(source_engine).get_columns(model.__tablename__)}
    model_columns = set(model.__table__.columns.keys())
    selected_columns = sorted(source_columns & model_columns)
    quoted_columns = ", ".join(f'"{column}"' for column in selected_columns)

    with source_engine.connect() as connection:
        result = connection.execute(
            text(f'SELECT {quoted_columns} FROM "{model.__tablename__}"')
        )
        return [dict(row) for row in result.mappings().all()]


def reset_postgres_sequences():
    """Make future auto-increment IDs continue after the migrated IDs."""
    with db.engine.begin() as connection:
        for model in TABLES:
            table_name = model.__tablename__
            connection.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                    "COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) "
                    f'FROM "{table_name}"'
                ),
                {"table_name": table_name},
            )


def migrate():
    """Migrate SQLite rows into an empty PostgreSQL schema in FK order."""
    settings = dotenv_values(ROOT / ".env")
    postgres_url = settings.get("DATABASE_URL")
    if not postgres_url or not postgres_url.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL in .env")
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_PATH}")

    source_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
    try:
        source_rows = {model: read_source_rows(source_engine, model) for model in TABLES}
    finally:
        source_engine.dispose()

    with app.app_context():
        initialize_database()
        target_counts = {
            model.__tablename__: db.session.execute(
                text(f'SELECT COUNT(*) FROM "{model.__tablename__}"')
            ).scalar_one()
            for model in TABLES
        }
        if any(target_counts.values()):
            raise RuntimeError(
                f"PostgreSQL is not empty: {target_counts}. "
                "Stop instead of duplicating or overwriting data."
            )

        try:
            for model in TABLES:
                rows = source_rows[model]
                if rows:
                    db.session.execute(model.__table__.insert(), rows)
            db.session.commit()
            reset_postgres_sequences()
        except Exception:
            db.session.rollback()
            raise

        migrated_counts = {
            model.__tablename__: db.session.execute(
                text(f'SELECT COUNT(*) FROM "{model.__tablename__}"')
            ).scalar_one()
            for model in TABLES
        }
        print("Migration complete:", migrated_counts)


if __name__ == "__main__":
    migrate()
