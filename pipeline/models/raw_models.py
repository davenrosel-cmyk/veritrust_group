from typing import TypedDict, Optional, List


class RawOfficeRecord(TypedDict, total=False):
    OfficeId: str
    OfficeType: str
    Address1: Optional[str]
    Address2: Optional[str]
    Address3: Optional[str]
    Address4: Optional[str]
    Town: Optional[str]
    Postcode: Optional[str]
    Country: Optional[str]


class RawFirmRecord(TypedDict, total=False):
    Id: str
    PracticeName: str
    AuthorisationStatus: str
    SraNumber: str
    AuthorisationType: str
    OrganisationType: str
    CompanyRegNo: str
    Constitution: str
    Offices: List[RawOfficeRecord]


class NormalizedAddress(TypedDict):
    streetAddress: str
    addressLocality: str
    postalCode: str
    addressCountry: str


class NormalizedFirm(TypedDict):
    sraId: str
    sraNumber: str
    name: str
    regulatoryStatus: str
    authorisationType: str
    organisationType: str
    companyRegNo: str
    constitution: str


class NormalizedOffice(TypedDict):
    officeId: str
    firmSraId: str
    isHeadOffice: bool
    address: NormalizedAddress
