

import logging
from typing import List, Dict, Tuple


def _clean(value):
    if not value:
        return ""
    return " ".join(str(value).split())


def _build_address(office):
    street = " ".join(
        p for p in [
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


def normalise_records(records: List[dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Convert SRA records to canonical Tier‑0 firm + office lists.
    """
    firms = []
    offices = []

    for rec in records:
        firm_id = str(rec.get("Id") or "").strip()
        name = _clean(rec.get("PracticeName"))
        status = _clean(rec.get("AuthorisationStatus"))
        sra_num = str(rec.get("SraNumber") or "").strip()

        if not firm_id:
            logging.warning("Skipping record with no Id")
            continue

        firm = {
            "sraId": firm_id,
            "sraNumber": sra_num,
            "name": name,
            "regulatoryStatus": status,
            "authorisationType": rec.get("AuthorisationType"),
            "organisationType": rec.get("OrganisationType"),
            "companyRegNo": rec.get("CompanyRegNo"),
            "constitution": rec.get("Constitution"),
        }

        firms.append(firm)

        for office in rec.get("Offices") or []:
            office_id = str(office.get("OfficeId") or "").strip()
            if not office_id:
                continue

            addr = _build_address(office)

            offices.append({
                "officeId": office_id,
                "firmSraId": firm_id,
                "isHeadOffice": office.get("OfficeType") == "HO",
                "address": addr,
            })

    logging.info("Normalisation → %d firms, %d offices", len(firms), len(offices))
    return firms, offices
