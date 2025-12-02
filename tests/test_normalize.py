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

    f = firms[0].model_dump()
    o = offices[0].model_dump()

    assert f["sraId"] == "F123"
    assert f["name"] == "Test Firm"
    assert o["officeId"] == "O1"
    assert o["isHeadOffice"] is True
    assert o["address"]["addressLocality"] == "London"
