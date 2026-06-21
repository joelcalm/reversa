"""Tests for the evidence endpoint service (all four briefing modes + pagination)."""
import pytest

from app.core.config import LEY_30_1992_ID
from app.services import evidence as ev


def test_evidence_unreadable_incoming_amends(db, insert_norm, insert_relation):
    insert_norm("X")
    for src in ("A", "B", "C"):
        insert_norm(src)
        insert_relation(src, "X", "AMENDS", label="MODIFICA")
    # A mirror duplicate must collapse to one logical edge.
    insert_relation("A", "X", "AMENDS", direction="posteriores", detail="mirror")

    with db.session_scope() as conn:
        res = ev.get_evidence(conn, "unreadable-laws", norm_id="X", scope="state")

    assert res["total"] == 3
    assert all(i["target_norm"]["id"] == "X" for i in res["items"])
    assert all(i["relation"]["relation_type"] == "AMENDS" for i in res["items"])
    assert res["items"][0]["relation"]["relation_label_raw"] == "MODIFICA"


def test_evidence_omnibus_outgoing_amends(db, insert_norm, insert_relation):
    insert_norm("O")
    for tgt in ("T1", "T2"):
        insert_norm(tgt)
        insert_relation("O", tgt, "AMENDS")

    with db.session_scope() as conn:
        res = ev.get_evidence(conn, "omnibus-laws", norm_id="O", scope="state")

    assert res["total"] == 2
    assert all(i["source_norm"]["id"] == "O" for i in res["items"])


def test_evidence_dead_law_incoming_cites_from_live(db, insert_norm, insert_relation):
    insert_norm("R1", derog="S")  # ghost
    insert_norm("L1")
    insert_norm("L2")
    insert_relation("L1", "R1", "CITES")
    insert_relation("L2", "R1", "CITES")
    # A repealed citer must be excluded (source must be LIVE).
    insert_norm("DEAD", derog="S")
    insert_relation("DEAD", "R1", "CITES")

    with db.session_scope() as conn:
        res = ev.get_evidence(conn, "dead-law-dependencies", norm_id="R1", scope="state")

    assert res["total"] == 2
    src_ids = {i["source_norm"]["id"] for i in res["items"]}
    assert src_ids == {"L1", "L2"}


def test_evidence_blast_radius_defaults_to_ley30(db, insert_norm, insert_relation):
    insert_norm(LEY_30_1992_ID, title="Ley 30/1992", derog="S")
    insert_norm("L3")
    insert_relation("L3", LEY_30_1992_ID, "CITES", label="CITA")

    with db.session_scope() as conn:
        res = ev.get_evidence(conn, "ley-30-1992-blast-radius", scope="state")

    assert res["norm_id"] == LEY_30_1992_ID
    assert res["total"] == 1
    assert res["items"][0]["source_norm"]["id"] == "L3"


def test_evidence_pagination(db, insert_norm, insert_relation):
    insert_norm("X")
    for i in range(5):
        insert_norm(f"S{i}")
        insert_relation(f"S{i}", "X", "AMENDS")

    with db.session_scope() as conn:
        page1 = ev.get_evidence(conn, "unreadable-laws", norm_id="X", limit=2, offset=0)
        page2 = ev.get_evidence(conn, "unreadable-laws", norm_id="X", limit=2, offset=2)

    assert page1["total"] == 5 and page2["total"] == 5
    assert len(page1["items"]) == 2 and len(page2["items"]) == 2
    ids1 = {i["source_norm"]["id"] for i in page1["items"]}
    ids2 = {i["source_norm"]["id"] for i in page2["items"]}
    assert ids1.isdisjoint(ids2)


def test_evidence_unknown_key_raises(db):
    with db.session_scope() as conn:
        with pytest.raises(KeyError):
            ev.get_evidence(conn, "nope", norm_id="X")


def test_evidence_missing_norm_id_raises(db):
    with db.session_scope() as conn:
        with pytest.raises(ValueError):
            ev.get_evidence(conn, "unreadable-laws", norm_id=None)
