"""SQLAlchemy Core table definitions for the BOE knowledge graph.

We use Core (not the ORM) because the data model is small and read-mostly and the
briefing queries are explicit aggregates that benefit from being plain SQL.
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

norms = Table(
    "norms",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("official_number", Text),
    Column("rank_code", Text),
    Column("rank", Text),
    Column("scope_code", Text),
    Column("scope", Text),
    Column("department_code", Text),
    Column("department", Text),
    Column("disposition_date", Text),
    Column("publication_date", Text),
    Column("effective_date", Text),
    Column("repeal_date", Text),
    Column("annulment_date", Text),
    Column("exhausted_validity", Text),
    Column("estatus_derogacion", Text),
    Column("estatus_anulacion", Text),
    Column("vigencia_agotada", Text),
    Column("consolidation_status_code", Text),
    Column("consolidation_status", Text),
    Column("lifecycle_status", Text, nullable=False),
    Column("is_live", Integer, nullable=False),
    Column("is_repealed", Integer, nullable=False),
    Column("url_eli", Text),
    Column("url_html", Text),
    Column("last_updated", Text),
    Column("raw_json", Text),
    Column("created_at", Text),
    Column("updated_at", Text),
)

relations = Table(
    "relations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_norm_id", Text, nullable=False),
    Column("target_norm_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("relation_code", Text),
    Column("relation_label_raw", Text),
    Column("relation_detail_raw", Text),
    Column("api_direction", Text),
    Column("current_norm_id", Text),
    Column("target_known", Integer),
    Column("created_at", Text),
    UniqueConstraint(
        "source_norm_id",
        "target_norm_id",
        "relation_type",
        "relation_code",
        "relation_detail_raw",
        name="uq_relation_identity",
    ),
)

subjects = Table(
    "subjects",
    metadata,
    Column("code", Text, primary_key=True),
    Column("label", Text, nullable=False),
)

norm_subjects = Table(
    "norm_subjects",
    metadata,
    Column("norm_id", Text, nullable=False),
    Column("subject_code", Text, nullable=False),
    UniqueConstraint("norm_id", "subject_code", name="pk_norm_subjects"),
)

briefing_results = Table(
    "briefing_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("briefing_key", Text, nullable=False),
    Column("scope", Text, nullable=False),
    Column("payload_json", Text, nullable=False),
    Column("computed_at", Text, nullable=False),
)

raw_relation_labels = Table(
    "raw_relation_labels",
    metadata,
    Column("label", Text, primary_key=True),
    Column("normalized_type", Text),
    Column("count", Integer, nullable=False),
)

# Indexes for the graph aggregate queries and norm filters.
Index("ix_relations_source", relations.c.source_norm_id)
Index("ix_relations_target", relations.c.target_norm_id)
Index("ix_relations_type", relations.c.relation_type)
Index("ix_norms_is_live", norms.c.is_live)
Index("ix_norms_is_repealed", norms.c.is_repealed)
Index("ix_norms_scope", norms.c.scope)
Index("ix_norms_lifecycle", norms.c.lifecycle_status)
Index("ix_briefing_key_scope", briefing_results.c.briefing_key, briefing_results.c.scope)
