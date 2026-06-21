"""Briefing logic tests on a controlled synthetic graph."""
from app.core.config import LEY_30_1992_ID
from app.services import briefings as bf


def test_unreadable_counts_distinct_amenders(db, insert_norm, insert_relation):
    insert_norm("X")
    for src in ("A", "B", "C"):
        insert_norm(src)
        insert_relation(src, "X", "AMENDS")
    # A duplicate edge from A must not double-count.
    insert_relation("A", "X", "AMENDS", detail="dup-ignored-by-distinct")

    with db.session_scope() as conn:
        res = bf.compute_unreadable(conn, scope="state", limit=5)
    top = res["items"][0]
    assert top["id"] == "X"
    assert top["amending_count"] == 3


def test_neighborhood_dedupes_mirror_edges(db, insert_norm, insert_relation):
    insert_norm("A")
    insert_norm("B")
    insert_relation("A", "B", "AMENDS", direction="anteriores", detail="from A")
    insert_relation("A", "B", "AMENDS", direction="posteriores", detail="from B page")

    with db.session_scope() as conn:
        g = bf.build_neighborhood(conn, "B", limit=20)

    assert len(g["edges"]) == 1
    assert g["meta"]["edges_deduplicated"] == 1
    hub = next(n for n in g["nodes"] if n["data"]["id"] == "B")
    assert hub["data"]["is_hub"] is True


    insert_norm("O")
    for tgt in ("T1", "T2", "T3"):
        insert_norm(tgt)
        insert_relation("O", tgt, "AMENDS")

    with db.session_scope() as conn:
        res = bf.compute_omnibus(conn, scope="state", limit=5)
    top = res["items"][0]
    assert top["id"] == "O"
    assert top["target_count"] == 3


def test_dead_law_dependencies(db, insert_norm, insert_relation):
    # Live L1, L2 cite repealed R1. Live L4 exists but cites nothing dead.
    insert_norm("L1")
    insert_norm("L2")
    insert_norm("L4")
    insert_norm("R1", derog="S")  # repealed
    insert_relation("L1", "R1", "CITES")
    insert_relation("L2", "R1", "CITES")
    # An AMENDS edge to a repealed norm must NOT count as resting on dead law.
    insert_norm("L3")
    insert_relation("L3", "R1", "AMENDS")

    with db.session_scope() as conn:
        res = bf.compute_dead_law(conn, scope="state", limit=5)

    assert res["live_norms_count"] == 4  # L1, L2, L3, L4 (R1 is repealed)
    assert res["live_norms_citing_repealed_count"] == 2  # L1, L2
    assert res["percentage"] == 50.0
    assert res["top_ghost_norms"][0]["id"] == "R1"
    assert res["top_ghost_norms"][0]["live_citers"] == 2


def test_blast_radius_includes_live_citer(db, insert_norm, insert_relation):
    insert_norm(LEY_30_1992_ID, title="Ley 30/1992", derog="S")  # the repealed target
    insert_norm("L3")  # live citer
    insert_relation("L3", LEY_30_1992_ID, "CITES", label="CITA")
    # A repealed norm citing it should be excluded (source must be LIVE).
    insert_norm("DEAD", derog="S")
    insert_relation("DEAD", LEY_30_1992_ID, "CITES")

    with db.session_scope() as conn:
        res = bf.compute_blast_radius(conn, scope="state")

    assert res["total_live_direct_citers"] == 1
    assert res["citing_norms"][0]["id"] == "L3"
    assert res["ley_30_1992"]["lifecycle_status"] == "REPEALED"


def test_scope_filtering_excludes_autonomic(db, insert_norm, insert_relation):
    insert_norm("X", scope="Estatal")
    insert_norm("AUT", scope="Autonómico")
    insert_norm("A")
    insert_relation("A", "X", "AMENDS")
    insert_relation("A", "AUT", "AMENDS")

    with db.session_scope() as conn:
        state = bf.compute_unreadable(conn, scope="state", limit=5)
        allc = bf.compute_unreadable(conn, scope="all", limit=5)

    state_ids = {i["id"] for i in state["items"]}
    all_ids = {i["id"] for i in allc["items"]}
    assert "X" in state_ids and "AUT" not in state_ids
    assert "AUT" in all_ids
