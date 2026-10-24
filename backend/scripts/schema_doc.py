"""
The data dictionary (every table, column, constraint) as Markdown, generated
from the SQLAlchemy models — never typed by hand.

docs/06_data_model.md embeds the output between marker comments, and
tests/test_docs_match_code.py fails if the embedded text no longer matches
what this module produces from the current models. So adding a column or a
constraint without updating the document is caught by the test suite.

Regenerate with:   python scripts/schema_doc.py
(then paste the output between the markers in docs/06_data_model.md)

Note what this does NOT cover: indexes. Most indexes exist only in the
Alembic migrations (the models do not declare them), so they are described
by hand in the document and checked against the migration files instead.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql

SCHEMA_BEGIN = "<!-- BEGIN GENERATED: data-dictionary -->"
SCHEMA_END = "<!-- END GENERATED: data-dictionary -->"


def _type_name(column: Column) -> str:
    return column.type.compile(dialect=postgresql.dialect()).lower()


def _notes(column: Column) -> str:
    notes: list[str] = []
    if column.primary_key:
        notes.append("primary key")
    for fk in column.foreign_keys:
        action = f", on delete {fk.ondelete.lower()}" if fk.ondelete else ""
        notes.append(f"→ `{fk.target_fullname}`{action}")
    if column.unique:
        notes.append("unique")
    if column.server_default is not None:
        notes.append("default: database clock")
    elif column.default is not None and getattr(column.default, "is_scalar", False):
        value = column.default.arg
        notes.append(f"default: `{getattr(value, 'value', value)}`")
    return "; ".join(notes)


def _check_sql(constraint: CheckConstraint) -> str:
    return " ".join(str(constraint.sqltext).split())


def render_data_dictionary() -> str:
    import app.models  # noqa: F401  (registers every model on the metadata)
    from app.database.base import Base

    out: list[str] = [SCHEMA_BEGIN, ""]
    for name, table in sorted(Base.metadata.tables.items()):
        out.append(f"### `{name}`")
        out.append("")
        out.append("| Column | Type | Required | Notes |")
        out.append("| --- | --- | :---: | --- |")
        for column in table.columns:
            required = "yes" if not column.nullable else ""
            out.append(f"| `{column.name}` | {_type_name(column)} | {required} | {_notes(column)} |")
        out.append("")

        rules: list[str] = []
        for constraint in sorted(table.constraints, key=lambda c: str(c.name)):
            if isinstance(constraint, CheckConstraint):
                rules.append(f"`{constraint.name}` (check): `{_check_sql(constraint)}`")
            elif isinstance(constraint, UniqueConstraint):
                if constraint.name is None:
                    continue  # a single-column unique already shown in that column's notes
                cols = ", ".join(c.name for c in constraint.columns)
                rules.append(f"`{constraint.name}` (unique): `{cols}`")
            elif isinstance(constraint, ForeignKeyConstraint):
                continue  # already shown per column
        if rules:
            out.append("Constraints:")
            out.append("")
            out.extend(f"- {rule}" for rule in rules)
            out.append("")

    out.append(SCHEMA_END)
    return "\n".join(out)


if __name__ == "__main__":
    print(render_data_dictionary())
