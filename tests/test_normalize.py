import pytest
from pipeline.normalize import normalise_records


def test_normalize_basic_record():
    raw = [
        {
            "Id": "F123",
            "SraNumber": "999",
            "PracticeName": " Test Firm ",
            "AuthorisationStatus": "Active",
            "AuthorisationType": "Recognised Body",
            "OrganisationType": "LLP",
            "CompanyRegNo": "12345",
            "Constitution": "Partnership",
            "Offices": [
                {
                    "OfficeId": "O1",
                    "OfficeType": "HEAD OFFICE",
                    "Address1": "1 High Street",
                    "Town": "London",
                    "Postcode": "N1 1AA",
                    "Country": "UK",
                }
            ],
        }
    ]

    firms, offices = normalise_records(raw)

    assert len(firms) == 1
    assert len(offices) == 1

    firm = firms[0]
    office = offices[0]

    assert firm["sraId"] == "F123"
    assert firm["name"] == "Test Firm"
    assert office["officeId"] == "O1"
    assert office["isHeadOffice"] is True
    assert office["address"]["addressLocality"] == "London"
