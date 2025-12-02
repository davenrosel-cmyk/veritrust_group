import json
from pathlib import Path

from pipeline.jsonld_builder import (
    compute_canonical_json_hash,
    build_jsonld_graph,
)
from pipeline.utils.atomic_writer import atomic_write_json

from pipeline.models.jsonld_models import (
    OfficeModel,
    FirmModel,
    PostalAddressModel,
)


def test_canonical_hash_is_deterministic():
    data1 = {"b": 1, "a": 2}
    data2 = {"a": 2, "b": 1}

    h1 = compute_canonical_json_hash(data1)
    h2 = compute_canonical_json_hash(data2)

    assert h1 == h2


def test_build_jsonld_graph_structure():
    firm = FirmModel(
        sraId="F1",
        name="Firm One",
        regulatoryStatus="Active",
    )

    office = OfficeModel(
        officeId="O1",
        firmSraId="F1",
        isHeadOffice=True,
        address=PostalAddressModel(
            streetAddress="X",
            addressLocality="Town",
            postalCode="123",
            addressCountry="UK",
        ),
    )

    graph = build_jsonld_graph([firm], [office])

    assert "@graph" in graph
    assert len(graph["@graph"]) == 2  # 1 firm + 1 office


def test_atomic_write_json(tmp_path):
    path = tmp_path / "firms.jsonld"
    data = {"a": 1}

    atomic_write_json(path, data)

    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["a"] == 1
