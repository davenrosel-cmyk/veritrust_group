import json
from pathlib import Path
from pipeline.jsonld_builder import (
    compute_canonical_json_hash,
    build_jsonld_graph,
    _safe_write_json,
)


def test_canonical_hash_is_deterministic():
    data = {"b": 1, "a": 2}
    h1 = compute_canonical_json_hash(data)
    h2 = compute_canonical_json_hash({"a": 2, "b": 1})
    assert h1 == h2


def test_build_jsonld_graph_structure():
    firms = [
        {
            "sraId": "F1",
            "name": "Firm One",
            "regulatoryStatus": "Active",
        }
    ]

    offices = [
        {
            "officeId": "O1",
            "firmSraId": "F1",
            "isHeadOffice": True,
            "address": {
                "streetAddress": "X",
                "addressLocality": "Town",
                "postalCode": "123",
                "addressCountry": "UK",
            },
        }
    ]

    graph = build_jsonld_graph(firms, offices)

    assert "@graph" in graph
    assert len(graph["@graph"]) == 2  


def test_safe_write_json(tmp_path):
    path = tmp_path / "firms.jsonld"
    data = {"a": 1}
    _safe_write_json(path, data)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["a"] == 1
