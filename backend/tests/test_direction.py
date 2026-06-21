"""Edge-direction tests. These would catch reversed edges.

The same logical edge `A --AMENDS--> B` must be produced whether it is discovered
from A's `anteriores` (A modifies B) or from B's `posteriores` (B is modified by A).
"""
from app.services.parsers import parse_analysis


def _anteriores_payload(other_id: str, label: str):
    """Shape of an analisis payload where the current norm acts on `other_id`."""
    return [
        {
            "materias": [],
            "notas": [],
            "referencias": {
                "anteriores": [
                    {"anterior": [
                        {"id_norma": other_id, "relacion": {"codigo": "270", "texto": label},
                         "texto": "detail"}
                    ]}
                ],
                "posteriores": [],
            },
        }
    ]


def _posteriores_payload(other_id: str, label: str):
    """Shape where a later norm `other_id` acts on the current norm."""
    return [
        {
            "materias": [],
            "notas": [],
            "referencias": {
                "anteriores": [],
                "posteriores": [
                    {"posterior": [
                        {"id_norma": other_id, "relacion": {"codigo": "270", "texto": label},
                         "texto": "detail"}
                    ]}
                ],
            },
        }
    ]


def test_anterior_direction_current_is_source():
    # Current A has an `anteriores` MODIFICA targeting B -> A AMENDS B
    result = parse_analysis("A", _anteriores_payload("B", "MODIFICA"))
    assert len(result.relations) == 1
    rel = result.relations[0]
    assert rel.source_norm_id == "A"
    assert rel.target_norm_id == "B"
    assert rel.relation_type == "AMENDS"
    assert rel.api_direction == "anteriores"


def test_posterior_direction_other_is_source():
    # Current B has a `posteriores` SE MODIFICA by A -> A AMENDS B
    result = parse_analysis("B", _posteriores_payload("A", "SE MODIFICA"))
    assert len(result.relations) == 1
    rel = result.relations[0]
    assert rel.source_norm_id == "A"
    assert rel.target_norm_id == "B"
    assert rel.relation_type == "AMENDS"
    assert rel.api_direction == "posteriores"


def test_both_directions_produce_same_edge():
    from_anterior = parse_analysis("A", _anteriores_payload("B", "MODIFICA")).relations[0]
    from_posterior = parse_analysis("B", _posteriores_payload("A", "SE MODIFICA")).relations[0]
    assert (from_anterior.source_norm_id, from_anterior.target_norm_id, from_anterior.relation_type) == (
        from_posterior.source_norm_id,
        from_posterior.target_norm_id,
        from_posterior.relation_type,
    )


def test_dedupe_same_edge(insert_relation, db):
    from sqlalchemy import text

    a_rel = parse_analysis("A", _anteriores_payload("B", "MODIFICA")).relations[0]
    p_rel = parse_analysis("B", _posteriores_payload("A", "MODIFICA")).relations[0]
    from app.services.ingestion import _insert_relations

    with db.session_scope() as conn:
        _insert_relations(conn, [a_rel, p_rel])
    with db.session_scope() as conn:
        count = conn.execute(
            text(
                "SELECT COUNT(*) FROM relations WHERE source_norm_id='A' "
                "AND target_norm_id='B' AND relation_type='AMENDS'"
            )
        ).scalar()
    # Same identity (source/target/type/code/detail) collapses to a single row.
    assert count == 1
