"""
JSON‑LD Builder (Phase‑3)
 - deterministic canonical JSON
 - uses Pydantic ONLY for structure validation
 - inputs MUST be plain dicts
 - outputs MUST be plain dicts
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict
from collections import defaultdict

from pipeline.models.jsonld_models import (
    PostalAddressModel,
    OfficeModel,
    OfficeLD,
    FirmModel,
    FirmLD,
)

PUBLIC_FILES_BASE = "https://api.veritrustgroup.org/files/"
PUBLIC_ID_BASE = "https://api.veritrustgroup.org/id/"

VT_CONTEXT = {
    "@vocab": "https://veritrustgroup.org/def/tier0/",
    "schema": "https://schema.org/",
    "vt": "https://veritrustgroup.org/def/tier0/",
}


def compute_canonical_json_hash(data: dict) -> str:
    canonical_json = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _firm_iri(sra_id: str) -> str:
    return f"{PUBLIC_ID_BASE}firm/{sra_id}"


def _office_iri(office_id: str) -> str:
    return f"{PUBLIC_ID_BASE}office/{office_id}"


def _public_url(path: Path) -> str:
    return f"{PUBLIC_FILES_BASE}{path.name}"


def build_office_entity(model: OfficeModel) -> Dict:
    return OfficeLD(
        **{
            "@id": _office_iri(model.officeId),
            "officeId": model.officeId,
            "firm": {"@id": _firm_iri(model.firmSraId)},
            "isHeadOffice": model.isHeadOffice,
            "address": model.address.model_dump(),
            "sameAs": f"https://www.sra.org.uk/consumers/register/office/?id={model.officeId}",
        }
    ).model_dump(by_alias=True)


def build_firm_entity(model: FirmModel, office_nodes: List[Dict]) -> Dict:
    return FirmLD(
        **{
            "@id": _firm_iri(model.sraId),
            "name": model.name,
            "regulatoryStatus": model.regulatoryStatus,
            "sraId": model.sraId,
            "offices": office_nodes,
            "sameAs": f"https://www.sra.org.uk/consumers/register/organisation/?id={model.sraId}",
        }
    ).model_dump(by_alias=True)


def build_jsonld_graph(
    firms: List[Dict],
    offices: List[Dict],
) -> Dict:

    offices_by_firm = defaultdict(list)

    validated_offices = []
    for o in offices:
        try:
            office_model = OfficeModel(**o)
            validated_offices.append(office_model)
            offices_by_firm[office_model.firmSraId].append(office_model)
        except Exception as e:
            logging.warning(f"Skipping invalid office (JSON-LD): {e}")

    validated_firms = []
    for f in firms:
        try:
            firm_model = FirmModel(**f)
            validated_firms.append(firm_model)
        except Exception as e:
            logging.warning(f"Skipping invalid firm (JSON-LD): {e}")

    graph = []

    for firm in validated_firms:
        office_nodes = [
            build_office_entity(o)
            for o in offices_by_firm.get(firm.sraId, [])
        ]
        graph.append(build_firm_entity(firm, office_nodes))
        graph.extend(office_nodes)

    return {
        "@context": VT_CONTEXT,
        "@graph": graph,
    }


def _safe_write_json(path: Path, data: Dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except Exception as e:
        logging.error(f"Write failure {path}: {e}")
        if tmp.exists():
            tmp.unlink()
        raise


def build_and_save_jsonld(
    firms: List[Dict],
    offices: List[Dict],
    firms_output_path: Path,
    dataset_output_path: Path,
):
    firms_doc = build_jsonld_graph(firms, offices)
    firms_hash = compute_canonical_json_hash(firms_doc)
    logging.info(f"firms.jsonld SHA256 = {firms_hash}")

    _safe_write_json(firms_output_path, firms_doc)

    dataset_doc = {
        "@context": "https://schema.org/",
        "@id": "https://api.veritrustgroup.org/dataset/tier0-sra",
        "@type": "Dataset",
        "name": "VeriTrust Tier-0 SRA Canonical Dataset",
        "dateModified": datetime.now(timezone.utc).isoformat(),
        "distribution": [
            {
                "@type": "DataDownload",
                "contentUrl": _public_url(firms_output_path),
                "encodingFormat": "application/ld+json",
            }
        ],
    }

    _safe_write_json(dataset_output_path, dataset_doc)
