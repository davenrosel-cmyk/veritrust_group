"""
This test runs the pipeline run end-to-end but:

Uses a temporary config.yaml

Builds results on tmp_path

Does not connect to Railway or the internet at all
"""

import json
from pathlib import Path
from pipeline.run_pipeline import run
from pipeline.utils.config_loader import load_config


def test_pipeline_end_to_end(tmp_path, monkeypatch):
    # Create a temporary config.yaml inside the temporary project root
    config_path = tmp_path / "config.yaml"

    config_path.write_text(
        """
            input_file: "./response.txt"
            raw_output_dir: "./raw"
            normalized_output_dir: "./norm"
            jsonld_firms: "./norm/firms.jsonld"
            jsonld_dataset: "./norm/dataset.jsonld"
            jsonld_manifest: "./norm/manifest.jsonld"
            public_files_base: "https://api.test/files/"
            public_id_base: "https://api.test/id/"
            head_office_code: "HEAD OFFICE"
        """ 
    )

   
    fake_input = tmp_path / "response.txt"
    fake_input.write_text(
        json.dumps(
            [
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
            ]
        )
    )

   
    monkeypatch.chdir(tmp_path)

   
    run()

   
    cfg = load_config("config.yaml")

    
    assert Path(cfg["jsonld_firms"]).exists()
    assert Path(cfg["jsonld_dataset"]).exists()
    assert Path(cfg["jsonld_manifest"]).exists()

