
"""
Normalize raw SRA firm/office records into Tier‑0 canonical format.

Includes:
    - name cleanup
    - address construction
    - identifier preservation
    - head office identification
    - whitespace, punctuation, casing normalisation
"""

import logging
from typing import List, Tuple
from pathlib import Path
from pipeline.models.raw_models import (
    RawFirmRecord,
    RawOfficeRecord,
    NormalizedFirm,
    NormalizedOffice,
    NormalizedAddress,
)
# from constants import HEAD_OFFICE
from pipeline.utils.config_loader import load_config

cfg = load_config()
HEAD_OFFICE = cfg.get("head_office_code", "HEAD OFFICE")

def _clean(value) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _build_address(office: RawOfficeRecord) -> NormalizedAddress:
    street = " ".join(
        p
        for p in [
            office.get("Address1"),
            office.get("Address2"),
            office.get("Address3"),
            office.get("Address4"),
        ]
        if p
    )

    return {
        "streetAddress": _clean(street),
        "addressLocality": _clean(office.get("Town")),
        "postalCode": _clean(office.get("Postcode")),
        "addressCountry": _clean(office.get("Country")),
    }


def normalise_records(
    records: List[RawFirmRecord],
) -> Tuple[List[NormalizedFirm], List[NormalizedOffice]]:
    """
    Convert SRA raw records → canonical firm + office lists (Tier‑0)
    """
    firms: List[NormalizedFirm] = []
    offices: List[NormalizedOffice] = []

    for rec in records:
        firm_id = _clean(rec.get("Id"))
        if not firm_id:
            logging.warning("Skipping record with no Id")
            continue

        firms.append(
            {
                "sraId": firm_id,
                "sraNumber": _clean(rec.get("SraNumber")),
                "name": _clean(rec.get("PracticeName")),
                "regulatoryStatus": _clean(rec.get("AuthorisationStatus")),
                "authorisationType": _clean(rec.get("AuthorisationType")),
                "organisationType": _clean(rec.get("OrganisationType")),
                "companyRegNo": _clean(rec.get("CompanyRegNo")),
                "constitution": _clean(rec.get("Constitution")),
            }
        )

        for office in rec.get("Offices") or []:
            office_id = _clean(office.get("OfficeId"))
            if not office_id:
                continue

            address = _build_address(office)

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
