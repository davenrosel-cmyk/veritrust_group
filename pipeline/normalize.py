"""
Normalize raw SRA firm/office records into Tier‑0 canonical format.

Improvements applied based on Feedback v3:
    - Full Pydantic validation (no dicts)
    - Removal of validate.py dependency
    - Strict data integrity checks
    - Canonical normalized models
    - Head office identification (config-driven)
    - Whitespace & casing cleanup
    - Absolute imports (ready for packaging)
"""

import logging
from typing import List

from pydantic import BaseModel, Field, ValidationError
from pipeline.utils.config_loader import load_config

from pipeline.models.raw_models import RawOfficeRecord
from pipeline.models.raw_models import RawFirmRecord, NormalizedFirm, NormalizedOffice, NormalizedAddress



cfg = load_config()
HEAD_OFFICE = cfg.head_office_code

class NormalizedAddress(BaseModel):
    streetAddress: str = Field(..., min_length=1)
    addressLocality: str = Field(..., min_length=1)
    postalCode: str = Field(..., min_length=1)
    addressCountry: str = Field(..., min_length=1)


class NormalizedOffice(BaseModel):
    officeId: str = Field(..., min_length=1)
    firmSraId: str = Field(..., min_length=1)
    isHeadOffice: bool
    address: NormalizedAddress


class NormalizedFirm(BaseModel):
    sraId: str = Field(..., min_length=1)
    sraNumber: str = ""
    name: str = Field(..., min_length=1)
    regulatoryStatus: str = ""
    authorisationType: str = ""
    organisationType: str = ""
    companyRegNo: str = ""
    constitution: str = ""


def _clean(value) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


from pydantic import ValidationError

def _build_address(office: RawOfficeRecord) -> NormalizedAddress | None:
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

    try:
        return NormalizedAddress(
            streetAddress=_clean(street),
            addressLocality=_clean(office.get("Town")),
            postalCode=_clean(office.get("Postcode")),
            addressCountry=_clean(office.get("Country")),
        )
    except ValidationError as e:
        logging.error(
            f"Office validation failed for firm {office.get('FirmId')} "
            f"office {office.get('OfficeId')}: {e}"
        )
        return None







def normalise_records(records: List[dict]) -> tuple[List[NormalizedFirm], List[NormalizedOffice]]:
    """
    Normalize raw SRA records → Tier-0 canonical models (validated via Pydantic)

    Args:
        records (List[dict]): Raw SRA dataset loaded from fetch_sra

    Returns:
        (firms, offices):
            firms: List[NormalizedFirm]
            offices: List[NormalizedOffice]

    Raises:
        ValidationError: If a record or office fails schema validation
    """
    firms: List[NormalizedFirm] = []
    offices: List[NormalizedOffice] = []

    for idx, rec in enumerate(records):
        firm_id = _clean(rec.get("Id"))
        if not firm_id:
            logging.warning("Skipping raw record with no Id at index %d", idx)
            continue

        try:
            firm = NormalizedFirm(
                sraId=firm_id,
                sraNumber=_clean(rec.get("SraNumber")),
                name=_clean(rec.get("PracticeName")),
                regulatoryStatus=_clean(rec.get("AuthorisationStatus")),
                authorisationType=_clean(rec.get("AuthorisationType")),
                organisationType=_clean(rec.get("OrganisationType")),
                companyRegNo=_clean(rec.get("CompanyRegNo")),
                constitution=_clean(rec.get("Constitution")),
            )
            firms.append(firm)

        except ValidationError as ve:
            logging.error("Firm validation failed at index %d: %s", idx, ve)
            raise

       
        for office in rec.get("Offices") or []:
            office_id = _clean(office.get("OfficeId"))
            if not office_id:
                logging.warning("Skipping office with no OfficeId in firm %s", firm_id)
                continue

            try:
                # addr = _build_address(office)
                addr = _build_address(office)
                if addr is None:
                    continue

                office_obj = NormalizedOffice(
                    officeId=office_id,
                    firmSraId=firm_id,
                    isHeadOffice=office.get("OfficeType") == HEAD_OFFICE,
                    address=addr,
                )
                offices.append(office_obj)

            except ValidationError as ve:
                logging.error(
                    "Office validation failed for firm %s office %s: %s",
                    firm_id,
                    office_id,
                    ve,
                )
                raise

    logging.info("Normalisation OK → %d firms, %d offices", len(firms), len(offices))
    return firms, offices
