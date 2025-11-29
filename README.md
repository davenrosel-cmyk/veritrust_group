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
veritrust-Tier0/
├── pipeline/                    # Main pipeline code
│   ├── models/                  # Data models
│   │   ├── jsonld_models.py     # JSON-LD models
│   │   └── raw_models.py        # Raw data models
│   ├── utils/                   # Utility modules
│   │   └── config_loader.py     # Configuration loader
│   ├── constants.py             # Constants and configuration
│   ├── fetch_sra.py             # SRA data fetching
│   ├── normalize.py             # Data normalization
│   ├── validate.py              # SHACL validation
│   ├── jsonld_builder.py        # JSON-LD file generation
│   ├── manifest_builder.py      # Manifest and signature generation
│   └── run_pipeline.py          # Main pipeline execution
│
├── tests/                       # Test suite
│   ├── test_normalize.py        # Normalization tests
│   ├── test_jsonld_builder.py   # JSON-LD builder tests
│   ├── test_manifest_builder.py # Manifest builder tests
│   └── test_pipeline.py         # End-to-end pipeline tests
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
│   │   ├── firms.jsonld
│   │   ├── dataset.jsonld
│   │   └── manifest.jsonld
│   ├── firms.jsonld             # JSON-LD output for firms
│   └── dataset.jsonld           # Complete JSON-LD output
│
├── ontology/                    # Ontology definitions
│   └── veritrust-min.ttl        # VeriTrust minimal ontology
│
├── shapes/                      # SHACL Shapes
│   └── tier0-shapes.ttl         # Tier-0 validation shapes
│
├── config.yaml                  # Configuration file
├── pytest.ini                   # Pytest configuration
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

### Configuration

The pipeline uses a flexible configuration system via `config.yaml` located in the project root. This replaces hardcoded values and makes the pipeline portable across different environments.

**Configuration File (`config.yaml`):**

```yaml
input_file: "./input/response.txt"
raw_output_dir: "./output/raw"
normalized_output_dir: "./output/normalized"
jsonld_firms: "./output/normalized/firms.jsonld"
jsonld_dataset: "./output/normalized/dataset.jsonld"
jsonld_manifest: "./output/normalized/manifest.jsonld"
public_files_base: "https://api.veritrustgroup.org/files/"
public_id_base: "https://api.veritrustgroup.org/id/"
head_office_code: "HEAD OFFICE"
```

**Configuration Parameters:**
- `input_file`: Path to the SRA input data file
- `raw_output_dir`: Directory for storing raw data snapshots
- `normalized_output_dir`: Directory for normalized intermediate files
- `jsonld_firms`: Output path for firms JSON-LD file
- `jsonld_dataset`: Output path for complete dataset JSON-LD file
- `jsonld_manifest`: Output path for manifest JSON-LD file
- `public_files_base`: Base URL for public file hosting
- `public_id_base`: Base URL for entity identifiers
- `head_office_code`: Code used to identify head offices

**Note:** You can customize these paths for different deployment environments without modifying source code.

### Main Dependencies

- `pydantic`: Data validation and modeling
- `python-dateutil`: Date processing
- `cryptography`: Digital signatures and encryption
- `PyYAML`: YAML configuration loader. Loads the `config.yaml` file used across the pipeline.
- `pytest`: Testing framework. Provides unit tests, integration tests, and end‑to‑end pipeline verification.
- `pytest-cov`: Coverage reporting. Generates coverage metrics for the entire project.
### Run Pipeline

**Before running the pipeline, ensure:**
1. `config.yaml` exists in the project root (see Configuration section above)
2. Input data file exists at the path specified in `config.yaml` (default: `input/response.txt`)

**Execute the pipeline:**
```bash
python pipeline/run_pipeline.py
```

The pipeline will:
1. Load configuration from `config.yaml`
2. Fetch and process SRA data
3. Generate all output files in the configured directories
4. Log progress and completion status

### Input Files

Before execution, ensure the SRA data file exists at the path specified in `config.yaml`:
```
input/response.txt
```

**Note:** The input file path can be customized in `config.yaml` for different environments.

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

### Configuration System

The pipeline uses a flexible YAML-based configuration system (`config.yaml`) that replaces hardcoded values. This makes the pipeline:

- **Portable**: Easy to deploy across different environments
- **Maintainable**: Configuration changes don't require code modifications
- **Testable**: Tests can use temporary configuration files

The configuration is loaded via `pipeline/utils/config_loader.py`, which:
- Loads YAML configuration from `config.yaml`
- Validates file existence
- Returns configuration as a dictionary
- Supports future environment variable overrides

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

The project includes a comprehensive test suite covering all critical components of the pipeline. Tests are located in the `tests/` directory and use `pytest` as the testing framework.

### Running Tests

**Run all tests with coverage:**
```bash
pytest --cov=. --cov-report=term
```

**Run specific test files:**
```bash
# Test normalization logic
pytest tests/test_normalize.py

# Test JSON-LD builder
pytest tests/test_jsonld_builder.py

# Test manifest builder
pytest tests/test_manifest_builder.py

# Test end-to-end pipeline
pytest tests/test_pipeline.py
```

**Run tests in verbose mode:**
```bash
pytest -v
```

### Test Suite Overview

#### 1. `test_normalize.py` - Normalization Tests
Tests the core normalization logic in `normalize.py`:
- Name cleaning and standardization
- Address construction and formatting
- Identifier extraction and validation
- Head office identification
- Edge cases and data transformation accuracy

**Key Test Cases:**
- Basic record normalization
- Whitespace and punctuation handling
- Address field mapping
- Head office detection

#### 2. `test_jsonld_builder.py` - JSON-LD Builder Tests
Tests JSON-LD generation in `jsonld_builder.py`:
- Canonical JSON hash computation (deterministic)
- JSON-LD graph structure validation
- Schema.org compliance
- File writing operations

**Key Test Cases:**
- Hash determinism (same data produces same hash)
- Graph structure correctness
- Safe file writing

#### 3. `test_manifest_builder.py` - Manifest Builder Tests
Tests manifest generation in `manifest_builder.py`:
- Manifest file creation
- Distribution metadata
- Context and structure validation

**Key Test Cases:**
- Manifest file generation
- Distribution array structure
- JSON-LD context presence

#### 4. `test_pipeline.py` - End-to-End Pipeline Tests
Tests the complete pipeline workflow:
- Full pipeline execution
- Configuration loading
- Output file generation
- Integration between all stages

**Key Test Cases:**
- End-to-end pipeline run with temporary config
- Output file existence verification
- Isolated test environment (no external dependencies)

### Test Configuration

The test suite is configured via `pytest.ini`:
```ini
[pytest]
addopts = -q
python_files = test_*.py
pythonpath = .
```

### Test Coverage

The test suite focuses on:
- **Edge Cases**: Handling of unusual or boundary data
- **Data Transformation Accuracy**: Ensuring normalization and JSON-LD conversion are correct
- **Integration**: Verifying all pipeline stages work together
- **Isolation**: Tests run independently without external dependencies

### Data Integrity Checks

After pipeline execution, you can:

1. **Check Manifest File**: Verify hash and signature
2. **Validate JSON-LD**: Use JSON-LD validation tools
3. **SHACL Validation**: Run SHACL validation on output data
4. **Run Test Suite**: Execute all tests to verify pipeline integrity

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
