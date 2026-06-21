"""API smoke tests using FastAPI's TestClient against a synthetic DB."""
from fastapi.testclient import TestClient

from app.core.config import LEY_30_1992_ID


def _client(db):
    # Import app after the temp DB env is set by the `db` fixture.
    from app.main import app

    return TestClient(app)


def _seed(db, insert_norm, insert_relation):
    insert_norm("X")
    insert_norm("O")
    insert_norm("R1", derog="S")
    insert_norm(LEY_30_1992_ID, title="Ley 30/1992", derog="S")
    for src in ("A", "B"):
        insert_norm(src)
        insert_relation(src, "X", "AMENDS")
    insert_relation("O", "X", "AMENDS")
    insert_relation("A", "R1", "CITES")
    insert_relation("B", LEY_30_1992_ID, "CITES", label="CITA")


def test_health(db):
    client = _client(db)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_summary(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)
    r = client.get("/api/summary")
    assert r.status_code == 200
    body = r.json()
    for key in (
        "total_norms",
        "total_relations",
        "relation_counts_by_type",
        "lifecycle_counts",
        "default_scope",
    ):
        assert key in body
    assert body["total_norms"] >= 5


def test_data_quality_endpoint(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)
    r = client.get("/api/data-quality")
    assert r.status_code == 200
    body = r.json()
    for key in (
        "total_norms",
        "total_relations",
        "relation_counts_by_type",
        "lifecycle_counts",
        "unknown_target_relations",
        "labels",
        "other_label_occurrences",
    ):
        assert key in body


def test_briefing_endpoints_structure(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)

    r1 = client.get("/api/briefings/unreadable-laws?scope=state&limit=5")
    assert r1.status_code == 200
    assert "items" in r1.json()

    r2 = client.get("/api/briefings/omnibus-laws?scope=state&limit=5")
    assert r2.status_code == 200
    assert "items" in r2.json()

    r3 = client.get("/api/briefings/dead-law-dependencies?scope=state")
    body3 = r3.json()
    for key in ("live_norms_count", "live_norms_citing_repealed_count", "percentage", "top_ghost_norms"):
        assert key in body3

    r4 = client.get("/api/briefings/ley-30-1992-blast-radius?scope=state")
    body4 = r4.json()
    assert "total_live_direct_citers" in body4
    assert "citing_norms" in body4


def test_cleanup_impact_endpoint(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)
    r = client.get("/api/briefings/ley-30-1992-cleanup-impact?scope=state")
    assert r.status_code == 200
    body = r.json()
    for key in ("denominator_live_norms", "before", "ley_30_1992", "after_simulated_cleanup"):
        assert key in body
    assert "repeal_context" in body["ley_30_1992"]


def test_evidence_endpoint(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)
    r = client.get("/api/briefings/unreadable-laws/evidence?norm_id=X&scope=state&limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["norm_id"] == "X"
    assert "items" in body and "total" in body

    r2 = client.get("/api/briefings/ley-30-1992-blast-radius/evidence?scope=state")
    assert r2.status_code == 200
    assert r2.json()["norm_id"] == LEY_30_1992_ID

    r3 = client.get("/api/briefings/does-not-exist/evidence?norm_id=X")
    assert r3.status_code == 404


def test_graph_endpoint(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)
    r = client.get("/api/graph/briefing/unreadable-laws?scope=state")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body and "edges" in body
    if body["edges"]:
        assert set(body["edges"][0]["data"].keys()) >= {
            "id", "source", "target", "relation_type",
        }


def test_graph_endpoint_unknown_key(db):
    client = _client(db)
    r = client.get("/api/graph/briefing/does-not-exist")
    assert r.status_code == 404


def test_norm_detail_and_neighborhood(db, insert_norm, insert_relation):
    _seed(db, insert_norm, insert_relation)
    client = _client(db)

    r = client.get("/api/norms/X")
    assert r.status_code == 200
    assert r.json()["metrics"]["amended_by_count"] == 3  # A, B, O

    r2 = client.get("/api/norms/X/neighborhood")
    assert r2.status_code == 200
    assert "nodes" in r2.json()

    r3 = client.get("/api/norms/NOPE")
    assert r3.status_code == 404
