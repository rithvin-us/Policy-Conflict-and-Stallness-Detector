"""Database engine, session factory, and declarative base.

SQLite by default (file-based, zero-config); swap ``DATABASE_URL`` for Postgres or
SingleStore in production. ``check_same_thread`` is disabled so the dev SQLite file
works under FastAPI's threadpool.

SingleStore notes: it speaks the MySQL wire protocol but has two DDL quirks this
module papers over so ``create_all`` succeeds unchanged:
  * ``VARCHAR`` requires an explicit length — unlengthed ``String`` columns get a
    default via the ``@compiles`` hook below.
  * ``FOREIGN KEY`` constraints are unsupported — they are stripped from the
    metadata in ``init_db`` (ORM relationship joins are resolved first, so this
    only affects emitted DDL, not query behaviour).
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import String, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# MySQL-family dialects (SingleStore included) reject VARCHAR without a length.
# Give any unlengthed String a sane default so the shared models compile there
# without per-column lengths. SQLite/Postgres compilation is untouched.
_DEFAULT_VARCHAR_LEN = 1024


@compiles(String, "singlestoredb")
@compiles(String, "mysql")
def _string_with_default_length(element, compiler, **kw):  # noqa: ANN001
    if element.length is None:
        return f"VARCHAR({_DEFAULT_VARCHAR_LEN})"
    return compiler.visit_VARCHAR(element, **kw)


_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False,
                            class_=Session)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register on Base.metadata before create_all.
    from app import models  # noqa: F401

    # SingleStore has no FOREIGN KEY support. Resolve relationship join conditions
    # first (configure_mappers reads the ForeignKey objects), then drop the FK
    # constraints from the DDL so create_all doesn't emit unsupported syntax.
    if engine.dialect.name.startswith("singlestore"):
        from sqlalchemy.orm import configure_mappers
        from sqlalchemy.schema import ForeignKeyConstraint

        configure_mappers()
        for table in Base.metadata.tables.values():
            for constraint in list(table.constraints):
                if isinstance(constraint, ForeignKeyConstraint):
                    table.constraints.discard(constraint)

    Base.metadata.create_all(bind=engine)
