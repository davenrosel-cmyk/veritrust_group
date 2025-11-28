from typing import Optional, List, Dict
from pydantic import BaseModel, Field



class PostalAddressModel(BaseModel):
    streetAddress: str
    addressLocality: Optional[str] = None
    addressRegion: Optional[str] = None
    postalCode: Optional[str] = None
    addressCountry: Optional[str] = "UK"


# ---------------------------------------------------------
# NORMALIZED OFFICE (after Phase 1)
# → converts to JSON-LD OfficeLD
# ---------------------------------------------------------

class OfficeModel(BaseModel):
    officeId: str
    firmSraId: str
    isHeadOffice: bool = False
    address: PostalAddressModel


class OfficeLD(BaseModel):
    id: str = Field(alias="@id")
    type: List[str] = Field(alias="@type", default=["vt:RegulatedOffice", "schema:PostalAddress"])

    officeId: str
    firm: Dict
    isHeadOffice: bool
    address: Dict
    sameAs: Optional[str] = None


# ---------------------------------------------------------
# NORMALIZED FIRM (after Phase 1)
# → converts to JSON-LD FirmLD
# ---------------------------------------------------------

class FirmModel(BaseModel):
    sraId: str
    name: str
    regulatoryStatus: str

   
    authorisationType: Optional[str] = None
    organisationType: Optional[str] = None
    companyRegNo: Optional[str] = None
    constitution: Optional[str] = None


class FirmLD(BaseModel):
    id: str = Field(alias="@id")
    type: List[str] = Field(alias="@type", default=["vt:RegulatedFirm", "schema:LegalService"])

    name: str
    regulatoryStatus: str
    sraId: str

    offices: List[Dict]
    sameAs: Optional[str] = None
