

import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone


PUBLIC_FILES_BASE = "https://api.veritrustgroup.org/files/"


PUBLIC_ID_BASE = "https://api.veritrustgroup.org/id/"


VT_CONTEXT = {
    "@vocab": "https://schema.org/",
    "vt": "https://veritrustgroup.org/def/tier0/",
    "RegulatedFirm": "vt:RegulatedFirm",
    "RegulatedOffice": "vt:RegulatedOffice",
    "sraId": "vt:sraId",
    "officeId": "vt:officeId",
    "regulatoryStatus": "vt:regulatoryStatus",
    "isHeadOffice": "vt:isHeadOffice",
    "hasOffice": "vt:hasOffice",
    "firm": "vt:firm",
}




def _build_firm_id(sra_id: str) -> str:
    """Canonical Firm IRI used across all datasets (Tier‑0 + VeriLaw)."""
    return f"{PUBLIC_ID_BASE}firm/{sra_id}"


def _build_office_id(office_id: str) -> str:
    """Canonical Office IRI used across Tier‑0 + VeriLaw."""
    return f"{PUBLIC_ID_BASE}office/{office_id}"


def _public_file_url(local_path: Path) -> str:
    """
    Map a local output file to its public URL served by Railway.

    Example:
    output/firms.jsonld  →  https://api.veritrustgroup.org/files/firms.jsonld
    """
    return f"{PUBLIC_FILES_BASE}{local_path.name}"




def build_jsonld_dataset(
    firms: List[Dict],
    offices: List[Dict],
    firms_output_path: Path,
    dataset_output_path: Path,
) -> None:
    """
    Build:
        output/firms.jsonld
        output/dataset.jsonld

    firms.jsonld:
        @context = VT_CONTEXT
        @graph   = RegulatedFirm + RegulatedOffice entities

    dataset.jsonld:
        schema:Dataset descriptor that points to firms.jsonld
    """

    now_iso = datetime.now(timezone.utc).isoformat()

    
    offices_by_firm: Dict[str, List[Dict]] = {}
    for off in offices:
        fid = off["firmSraId"]
        offices_by_firm.setdefault(fid, []).append(off)

    jsonld_graph = []

    
    for firm in firms:
        sra_id = firm["sraId"]
        firm_iri = _build_firm_id(sra_id)

        
        firm_obj = {
            "@id": firm_iri,
            "@type": "RegulatedFirm",
            "sraId": sra_id,
            "name": firm["name"],
            "regulatoryStatus": firm["regulatoryStatus"],
        }

       
        firm_offices = []
        for off in offices_by_firm.get(sra_id, []):
            office_iri = _build_office_id(off["officeId"])

            office_obj = {
                "@id": office_iri,
                "@type": "RegulatedOffice",
                "officeId": off["officeId"],
                "firmSraId": off["firmSraId"],
                "isHeadOffice": off["isHeadOffice"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": off["address"]["streetAddress"],
                    "addressLocality": off["address"]["addressLocality"],
                    "postalCode": off["address"]["postalCode"],
                    "addressCountry": off["address"]["addressCountry"],
                }
            }

            firm_offices.append(office_obj)

        
        if firm_offices:
            firm_obj["hasOffice"] = [{"@id": o["@id"]} for o in firm_offices]

       
        jsonld_graph.append(firm_obj)
        jsonld_graph.extend(firm_offices)

   
    firms_doc = {
        "@context": VT_CONTEXT,
        "@graph": jsonld_graph,
    }

    firms_output_path.parent.mkdir(parents=True, exist_ok=True)
    with firms_output_path.open("w", encoding="utf-8") as f:
        json.dump(firms_doc, f, ensure_ascii=False, indent=2)

    logging.info("✔ firms.jsonld written → %s", firms_output_path)

   
    firms_public_url = _public_file_url(firms_output_path)

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
                "contentUrl": firms_public_url,
                "encodingFormat": "application/ld+json",
            }
        ],
    }

    with dataset_output_path.open("w", encoding="utf-8") as f:
        json.dump(dataset_doc, f, ensure_ascii=False, indent=2)

    logging.info("✔ dataset.jsonld written → %s", dataset_output_path)
