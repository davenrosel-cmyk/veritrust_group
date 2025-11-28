

import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
from collections import defaultdict


PUBLIC_FILES_BASE = "https://api.veritrustgroup.org/files/"


PUBLIC_ID_BASE = "https://api.veritrustgroup.org/id/"
from pipeline.models.jsonld_models import (
    PostalAddressModel,
    OfficeModel,
    OfficeLD,
    FirmModel,
    FirmLD,
)

VT_CONTEXT = {
    "@vocab": "https://veritrustgroup.org/def/tier0/",
    "schema": "https://schema.org/",
    "vt": "https://veritrustgroup.org/def/tier0/",
}





def _build_firm_iri(sra_id: str) -> str:
    return f"{PUBLIC_ID_BASE}firm/{sra_id}"


def _build_office_iri(office_id: str) -> str:
    return f"{PUBLIC_ID_BASE}office/{office_id}"


def _public_url(local_path: Path) -> str:
    """Convert local output path to Railway public URL."""
    return f"{PUBLIC_FILES_BASE}{local_path.name}"


# ENTITY BUILDERS (Firm → JSON-LD, Office → JSON-LD)


def build_office_entity(model: OfficeModel) -> Dict:
    office_iri = _build_office_iri(model.officeId)

    return OfficeLD(
        **{
            "@id": office_iri,
            "officeId": model.officeId,
            "firm": {"@id": _build_firm_iri(model.firmSraId)},
            "isHeadOffice": model.isHeadOffice,
            "address": model.address.model_dump(),
            "sameAs": f"https://www.sra.org.uk/consumers/register/office/?id={model.officeId}",
        }
    ).model_dump(by_alias=True)


def build_firm_entity(model: FirmModel, offices_jsonld: List[Dict]) -> Dict:
    firm_iri = _build_firm_iri(model.sraId)

    return FirmLD(
        **{
            "@id": firm_iri,
            "name": model.name,
            "regulatoryStatus": model.regulatoryStatus,
            "sraId": model.sraId,
            "offices": offices_jsonld,
            "sameAs": f"https://www.sra.org.uk/consumers/register/organisation/?id={model.sraId}",
        }
    ).model_dump(by_alias=True)



# CORE JSON-LD DATASET BUILDING


def build_jsonld_graph(
    firms: List[Dict],
    offices: List[Dict],
) -> Dict:
    """
    Convert validated Phase-1 normalized dicts
    → canonical JSON-LD graph using Pydantic models.
    """


    offices_by_firm = defaultdict(list)

    validated_offices = []
    for o in offices:
        try:
            office_model = OfficeModel(**o)
            validated_offices.append(office_model)
            offices_by_firm[office_model.firmSraId].append(office_model)
        except Exception as e:
            logging.warning(f"Skipping invalid office record: {e}")

    validated_firms = []
    for f in firms:
        try:
            firm_model = FirmModel(**f)
            validated_firms.append(firm_model)
        except Exception as e:
            logging.warning(f"Skipping invalid firm record: {e}")

    graph = []

    for firm in validated_firms:
        firm_office_entities = [
            build_office_entity(o) for o in offices_by_firm.get(firm.sraId, [])
        ]

 
        firm_entity = build_firm_entity(firm, firm_office_entities)

        graph.append(firm_entity)
        graph.extend(firm_office_entities)

  
    return {
        "@context": VT_CONTEXT,
        "@graph": graph,
    }




def _safe_write_json(path: Path, data: Dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"✔ Written JSON-LD → {path}")
    except Exception as e:
        logging.error(f"❌ Failed to write JSON file {path}: {e}")
        raise



# TOP-LEVEL BUILD FUNCTION (called by run_pipeline.py)


def build_and_save_jsonld(
    firms: List[Dict],
    offices: List[Dict],
    firms_output_path: Path,
    dataset_output_path: Path,
):
    """
    Main entrypoint used by run_pipeline.py.
    Generates:
      - firms.jsonld (detailed graph)
      - dataset.jsonld (Dataset descriptor)
    """

 
    firms_doc = build_jsonld_graph(firms, offices)
    _safe_write_json(firms_output_path, firms_doc)


    now_iso = datetime.now(timezone.utc).isoformat()
    public_url = _public_url(firms_output_path)

    dataset_doc = {
        "@context": "https://schema.org/",
        "@id": "https://api.veritrustgroup.org/dataset/tier0-sra",
        "@type": "Dataset",
        "name": "VeriTrust Tier-0 SRA Canonical Dataset",
        "description": (
            "Nightly canonical transformation of SRA public organisation data "
            "into AI-ready JSON-LD."
        ),
        "creator": {
            "@type": "Organization",
            "name": "VeriTrust Group Limited",
        },
        "dateModified": now_iso,
        "distribution": [
            {
                "@type": "DataDownload",
                "contentUrl": public_url,
                "encodingFormat": "application/ld+json",
            }
        ],
    }

    _safe_write_json(dataset_output_path, dataset_doc)



    logging.info("✔ dataset.jsonld written → %s", dataset_output_path)
