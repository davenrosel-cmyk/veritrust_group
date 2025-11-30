"""
Normalize raw SRA firm/office records into Tier‑0 canonical dict format.

V3 Requirements:
    - Output MUST be plain dicts (SHACL compatibility)
    - Use defensive cleanup
    - Skip invalid offices (missing address fields) without crashing
    - HEAD_OFFICE imported from constants
"""

import logging
from typing import List, Tuple

from pipeline.constants import HEAD_OFFICE


def _clean(value) -> str:
    """Trim + normalize whitespace."""
    if not value:
        return ""
    return " ".join(str(value).split())


def _build_address(office: dict) -> dict:
    """
    Build canonical address dict.
    If all address fields are empty → return None (caller will skip office).
    """
    street = " ".join(
        p for p in [
            office.get("Address1"),
            office.get("Address2"),
            office.get("Address3"),
            office.get("Address4"),
        ] if p
    )

    addr = {
        "streetAddress": _clean(street),
        "addressLocality": _clean(office.get("Town")),
        "postalCode": _clean(office.get("Postcode")),
        "addressCountry": _clean(office.get("Country")),
    }

    # If the entire address is empty → invalid
    if not any(addr.values()):
        return None

    return addr


def normalise_records(
    records: List[dict],
) -> Tuple[List[dict], List[dict]]:
    """
    Convert SRA raw records → canonical firm + office lists (Tier‑0).
    Output MUST be dicts for JSON-LD, SHACL validation, and Phase‑4 compatibility.
    """

    firms: List[dict] = []
    offices: List[dict] = []

    for rec in records:
        firm_id = _clean(rec.get("Id"))
        if not firm_id:
            logging.warning("Skipping record with no Id")
            continue

        firm = {
            "sraId": firm_id,
            "sraNumber": _clean(rec.get("SraNumber")),
            "name": _clean(rec.get("PracticeName")),
            "regulatoryStatus": _clean(rec.get("AuthorisationStatus")),
            "authorisationType": _clean(rec.get("AuthorisationType")),
            "organisationType": _clean(rec.get("OrganisationType")),
            "companyRegNo": _clean(rec.get("CompanyRegNo")),
            "constitution": _clean(rec.get("Constitution")),
        }

        firms.append(firm)

        for office in rec.get("Offices") or []:
            office_id = _clean(office.get("OfficeId"))
            if not office_id:
                continue

            address = _build_address(office)
            if not address:
                logging.warning(f"Skipping office {office_id}: incomplete/empty address")
                continue

            offices.append(
                {
                    "officeId": office_id,
                    "firmSraId": firm_id,
                    "isHeadOffice": office.get("OfficeType") == HEAD_OFFICE,
                    "address": address,
                }
            )

    logging.info("Normalisation → %d firms, %d offices", len(firms), len(offices))
    return firms, offices
