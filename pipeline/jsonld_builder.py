"""
Build canonical VeriTrust Tier‑0 JSON‑LD output.

Implements:
    - Pydantic-based strict typing (validated upstream in normalize.py)
    - canonical IRIs (firm + office)
    - deterministic JSON‑LD serialization (Phase 4)
    - atomic write (Phase 3)
    - absolute imports
    - zero redundant validation

Inputs:
    firms   : List[FirmModel]
    offices : List[OfficeModel]

Outputs:
    firms.jsonld   : canonical entity graph (firms + offices)
    dataset.jsonld : dataset descriptor for public consumption
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

from pydantic import ValidationError

from pipeline.utils.config_loader import load_config
from pipeline.models.jsonld_models import (
    PostalAddressModel,
    OfficeModel,
    OfficeLD,
    FirmModel,
    FirmLD,
)

cfg = load_config()

PUBLIC_FILES_BASE = cfg.public_files_base
PUBLIC_ID_BASE = cfg.public_id_base


VT_CONTEXT = {
    "@vocab": "https://veritrustgroup.org/def/tier0/",
    "schema": "https://schema.org/",
    "vt": "https://veritrustgroup.org/def/tier0/",
}




def _iri_firm(sra_id: str) -> str:
    return f"{PUBLIC_ID_BASE}firm/{sra_id}"


def _iri_office(office_id: str) -> str:
    return f"{PUBLIC_ID_BASE}office/{office_id}"


def _public_url(path: Path) -> str:
    """Map a local file path → Railway public URL."""
    return f"{PUBLIC_FILES_BASE}{path.name}"




def compute_canonical_json_hash(data: dict) -> str:
    """
    Deterministic Phase‑4 hash:
      - sorted keys
      - minified separators
      - UTF‑8 bytes
    """
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()




def build_office_entity(model: OfficeModel) -> Dict:
    """
    Convert OfficeModel → JSON‑LD entity (OfficeLD).
    """
    office_iri = _iri_office(model.officeId)

    office_ld = OfficeLD(
        **{
            "@id": office_iri,
            "officeId": model.officeId,
            "firm": {"@id": _iri_firm(model.firmSraId)},
            "isHeadOffice": model.isHeadOffice,
            "address": model.address.model_dump(),
            "sameAs": f"https://www.sra.org.uk/consumers/register/office/?id={model.officeId}",
        }
    )
    return office_ld.model_dump(by_alias=True)


def build_firm_entity(model: FirmModel, office_entities: List[Dict]) -> Dict:
    """
    Convert FirmModel → JSON‑LD entity (FirmLD).
    """
    firm_iri = _iri_firm(model.sraId)

    firm_ld = FirmLD(
        **{
            "@id": firm_iri,
            "name": model.name,
            "legalName": model.name,
            "regulatoryStatus": model.regulatoryStatus,
            "sraId": model.sraId,
            "offices": office_entities,
            "sameAs": (
                f"https://www.sra.org.uk/consumers/register/organisation/?id={model.sraId}"
            ),
        }
    )

    return firm_ld.model_dump(by_alias=True)



def build_jsonld_graph(
    firms: List[FirmModel],
    offices: List[OfficeModel],
) -> Dict:
    """
    Build the full canonical JSON‑LD graph.

    NOTE:
        This function receives *validated Pydantic models*.
        If any record is invalid, normalize.py should have already rejected it.
    """

    offices_by_firm: Dict[str, List[OfficeModel]] = {}

    for off in offices:
        offices_by_firm.setdefault(off.firmSraId, []).append(off)

    graph = []

    for firm in firms:
        firm_office_entities = [
            build_office_entity(o)
            for o in offices_by_firm.get(firm.sraId, [])
        ]

        firm_entity = build_firm_entity(firm, firm_office_entities)

        graph.append(firm_entity)
        graph.extend(firm_office_entities)

    return {
        "@context": VT_CONTEXT,
        "@graph": graph,
    }




def _atomic_write_json(path: Path, data: Dict):
    """
    Atomic JSON writer:
      - write to <path>.tmp
      - replace() final
    """
    tmp = path.with_suffix(path.suffix + ".tmp")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        tmp.replace(path)
        logging.info(f"✔ Atomically written → {path}")

    except OSError as e:
        logging.error(f"Failed to write JSON file: {path} | {e}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise




def build_and_save_jsonld(
    firms: List[FirmModel],
    offices: List[OfficeModel],
    firms_output_path: Path,
    dataset_output_path: Path,
):
    """
    Generate and atomically write:
        - firms.jsonld
        - dataset.jsonld

    Both files include canonical Phase‑4 SHA‑256 hashes.
    """

    
    firms_doc = build_jsonld_graph(firms, offices)
    firms_hash = compute_canonical_json_hash(firms_doc)
    logging.info(f"✔ firms.jsonld canonical SHA‑256 = {firms_hash}")

    _atomic_write_json(firms_output_path, firms_doc)


    now_iso = datetime.now(timezone.utc).isoformat()
    public_url = _public_url(firms_output_path)

    dataset_doc = {
        "@context": "https://schema.org/",
        "@id": "https://api.veritrustgroup.org/dataset/tier0-sra",
        "@type": "Dataset",
        "name": "VeriTrust Tier‑0 SRA Canonical Dataset",
        "description": (
            "Nightly canonical transformation of SRA public organisation data "
            "into AI‑ready JSON‑LD."
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
        "canonicalSha256": firms_hash,
    }

    dataset_hash = compute_canonical_json_hash(dataset_doc)
    logging.info(f"✔ dataset.jsonld canonical SHA‑256 = {dataset_hash}")

    _atomic_write_json(dataset_output_path, dataset_doc)

    logging.info("✔ JSON‑LD build complete.")
