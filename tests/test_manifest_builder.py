import json
from pathlib import Path
from pipeline.manifest_builder import build_manifest_and_sign


def test_manifest_written(tmp_path):
    firms = tmp_path / "firms.jsonld"
    dataset = tmp_path / "dataset.jsonld"

    firms.write_text("{}")
    dataset.write_text("{}")

    manifest = tmp_path / "manifest.jsonld"

    build_manifest_and_sign(
        firms_path=firms,
        dataset_path=dataset,
        manifest_output_path=manifest,
    )

    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert "@context" in data
    assert "distribution" in data
    assert len(data["distribution"]) == 2
