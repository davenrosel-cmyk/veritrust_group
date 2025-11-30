import json
import textwrap
from pathlib import Path
from pipeline.run_pipeline import run
from pipeline.utils.config_loader import load_config

def test_pipeline_end_to_end(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

    # 1) Create config.yaml
    (tmp_path / "config.yaml").write_text(textwrap.dedent("""
        input_file: "./response.txt"
        raw_output_dir: "./raw"
        normalized_output_dir: "./norm"
        jsonld_firms: "./output/firms.jsonld"
        jsonld_dataset: "./output/dataset.jsonld"
        jsonld_manifest: "./norm/manifest.jsonld"
        public_files_base: "https://test/files/"
        public_id_base: "https://test/id/"
        head_office_code: "HEAD OFFICE"
    """))

    # 2) Input file
    (tmp_path / "response.txt").write_text(json.dumps([
        {
            "Id": "F1",
            "PracticeName": "Firm One",
            "AuthorisationStatus": "Active",
            "Offices": [
                {
                    "OfficeId": "O1",
                    "OfficeType": "HEAD OFFICE",
                    "Address1": "A",
                    "Town": "T",
                    "Postcode": "P",
                    "Country": "UK",
                }
            ],
        }
    ]))

    # 3) Run pipeline
    run()

    # 4) Reload config using attribute access
    cfg = load_config("config.yaml")

    assert Path(cfg.raw_output_dir).exists()
    assert Path(cfg.normalized_output_dir, "firms.json").exists()
    assert Path(cfg.normalized_output_dir, "offices.json").exists()
    assert Path(cfg.jsonld_firms).exists()
    assert Path(cfg.jsonld_dataset).exists()
    assert Path(cfg.jsonld_manifest).exists()
