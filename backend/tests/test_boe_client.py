"""BOE list pagination helpers."""
from app.services.boe_client import list_items


def test_list_items_from_array():
    payload = [{"identificador": "A"}, {"identificador": "B"}]
    assert len(list_items(payload)) == 2


def test_list_items_wrapped():
    payload = {"status": {"code": "200"}, "data": [{"identificador": "X"}]}
    assert list_items(payload)[0]["identificador"] == "X"


def test_list_items_empty():
    assert list_items([]) == []
    assert list_items(None) == []
