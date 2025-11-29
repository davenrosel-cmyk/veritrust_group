# VeriTrust Group - SRA Data Processing Pipeline

## 📋 Project Overview

This repository contains a production-grade Tier-0 pipeline for transforming the Solicitors Regulation Authority (SRA) public dataset into canonical, normalized, SHACL-validated, JSON-LD datasets published nightly by VeriTrust Group Ltd.

### Key Features

- ✅ **Canonical Data**: Only source facts, no enrichments or derived concepts
- ✅ **Standard Normalization**: Clean and standardize names, addresses, and identifiers
- ✅ **SHACL Validation**: Data validation using SHACL Shapes
- ✅ **Schema.org Compliant**: JSON-LD output conforming to Schema.org standards
- ✅ **Digital Signatures**: Manifest generation with SHA-256 and optional RSA signature
- ✅ **AI-Ready**: ai.txt and robots.txt files for automated discovery

---

## 🏗️ System Architecture

The pipeline executes in 6 main stages:

### Stage 1: Data Fetch
- Load SRA data from local file
- Save raw version for audit and tracking

### Stage 2: Normalization
- Normalize firm and office information:
  - Clean and standardize names
  - Build standard UK addresses
  - Extract and validate identifiers (sraId, officeId)
  - Normalize statuses and standard fields

### Stage 3: Validation
- Validate with SHACL Shapes (Tier-0)
- Check mandatory fields and basic data types
- Filter invalid records

### Stage 4: JSON-LD Build
- Convert to Schema.org compliant entities:
  - `schema:LegalService`
  - `schema:Organization`
  - `schema:PostalAddress`
  - `schema:ContactPoint`
  - VeriTrust Tier-0 ontology extensions

### Stage 5: Manifest & Signature
- Generate Manifest with canonical JSON
- Calculate SHA-256 for data integrity
- Optional RSA signature

### Stage 6: AI Discovery Files
- Generate `/ai.txt` listing public dataset URLs
- Generate `/robots.txt` to enable crawler access

---

## 📁 Project Structure

```
venv/
├── pipeline/                    # Main pipeline code
│   ├── models/                  # Data models
│   │   ├── jsonld_models.py     # JSON-LD models
│   │   └── raw_models.py        # Raw data models
│   ├── constants.py             # Constants and configuration
│   ├── fetch_sra.py             # SRA data fetching
│   ├── normalize.py             # Data normalization
│   ├── validate.py              # SHACL validation
│   ├── jsonld_builder.py        # JSON-LD file generation
│   ├── manifest_builder.py      # Manifest and signature generation
│   └── run_pipeline.py          # Main pipeline execution
│
├── input/                       # Input data
│   └── response.txt             # SRA data file
│
├── output/                      # Processed outputs
│   ├── raw/                     # Raw data (for auditing)
│   │   └── sra-YYYYMMDD.json
│   ├── normalized/              # Normalized data
│   │   ├── firms.json
│   │   ├── offices.json
│   │   └── manifest.jsonld
│   ├── firms.jsonld             # JSON-LD output for firms
│   ├── dataset.jsonld           # Complete JSON-LD output
│   └── manifest.jsonld          # Manifest with signature
│
├── ontology/                    # Ontology definitions
│   └── veritrust-min.ttl        # VeriTrust minimal ontology
│
├── shapes/                      # SHACL Shapes
│   └── tier0-shapes.ttl         # Tier-0 validation shapes
│
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🚀 Setup and Usage

### Prerequisites

- Python 3.11
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Main dependencies:
- `pydantic`: Data validation and modeling
- `python-dateutil`: Date processing
- `cryptography`: Digital signatures and encryption

### Run Pipeline

```bash
python pipeline/run_pipeline.py
```

### Input Files

Before execution, ensure the SRA data file exists at:
```
input/response.txt
```

### Output Files

After successful execution, the following files are generated in the `output/` directory:

#### JSON-LD
- `firms.jsonld`: List of law firms in JSON-LD format
- `dataset.jsonld`: Complete dataset with all entities

#### Manifest
- `manifest.jsonld`: Manifest containing:
  - SHA-256 hash for data integrity
  - RSA signature (if enabled)
  - Publication metadata

#### Normalized Data
- `normalized/firms.json`: Normalized firms
- `normalized/offices.json`: Normalized offices

#### Raw Data (for auditing)
- `raw/sra-YYYYMMDD.json`: Raw version of fetched data

---

## 🔧 Technical Details

### Data Models

#### Raw Models (`raw_models.py`)
- `RawFirmRecord`: Raw firm data structure from SRA
- `RawOfficeRecord`: Raw office data structure

#### Normalized Models
- `NormalizedFirm`: Normalized firm
- `NormalizedOffice`: Normalized office
- `NormalizedAddress`: Standardized address

#### JSON-LD Models (`jsonld_models.py`)
- Schema.org compliant entities
- VeriTrust ontology extensions

### Validation

The system uses SHACL (Shapes Constraint Language) for validation:
- Mandatory field checks
- Data type validation
- Basic integrity rules

Shapes are defined in `shapes/tier0-shapes.ttl`.

### Standards Used

- **JSON-LD**: Linked data format
- **Schema.org**: Standard vocabulary for web entities
- **SHACL**: Shapes Constraint Language for validation
- **RDF/Turtle**: For ontology and shapes definition

---

## 🔐 Security and Integrity

### Hash and Signatures

- Each output file is hashed with SHA-256
- Manifest includes hash of all output files
- Optional RSA signature for authentication

### Auditing

- All raw data is stored in `output/raw/`
- Automatic file timestamping for change tracking
- Comprehensive logging for error tracking

---

## 📊 Deployment

### Railway Cron Job

The pipeline can be automatically executed on Railway:

**Schedule**: Every night at 02:00 UTC

```bash
python pipeline/run_pipeline.py
```

### Static File Hosting

- The `/output/` directory is served as the public dataset root
- `ai.txt` and `robots.txt` files enable automated discovery by search engines and AI

---

## 🧪 Testing and Validation

### Data Integrity Checks

After pipeline execution, you can:

1. **Check Manifest File**: Verify hash and signature
2. **Validate JSON-LD**: Use JSON-LD validation tools
3. **SHACL Validation**: Run SHACL validation on output data

---

## 📝 Logging

The system uses Python's standard `logging` module:

- Log level: `INFO`
- Logged information:
  - Number of records loaded
  - Normalization results
  - Validation results
  - Output file generation status

---

## 🔄 Workflow

```
1. Fetch SRA Data
   ↓
2. Normalize (names, addresses, identifiers)
   ↓
3. Validate (SHACL)
   ↓
4. Build JSON-LD (Schema.org)
   ↓
5. Generate Manifest + Hash + Signature
   ↓
6. Generate AI Discovery Files
   ↓
✅ Final output ready for publication
```

---

## 📚 Resources and Documentation

- [Schema.org](https://schema.org/) - Standard vocabulary
- [JSON-LD](https://json-ld.org/) - Linked data format
- [SHACL](https://www.w3.org/TR/shacl/) - Shapes Constraint Language
- [SRA](https://www.sra.org.uk/) - Solicitors Regulation Authority

---

## 👥 Team and License

**Developer**: VeriTrust Group Ltd

**License**: Copyright © VeriTrust

---

## 📞 Support

For questions and support, please contact the VeriTrust Group team.

---

## 🔄 Versions and Updates

This pipeline is continuously updated to:
- Improve normalization quality
- Add new validations
- Optimize performance
- Maintain compatibility with latest Schema.org standards

---

**Last Updated**: 2025
