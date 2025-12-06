# Invoice QC Service

Invoice Extraction & Quality Control Service - extracts structured data from PDF invoices and validates them against business rules.

## Quick Start

```powershell
cd invoice-qc-export
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python -m invoice_qc.cli full-run --pdf-dir pdfs --report report.json --separate --output-dir output
```

## Features

- PDF extraction with German B2B document support
- 12 validation rules
- CLI + REST API + React frontend
- Individual JSON files per invoice

## Structure

```
invoice-qc-export/
├── invoice_qc/          # Python source code
│   ├── models.py        # Pydantic data models
│   ├── utils.py         # Helper functions
│   ├── extractor.py     # PDF extraction
│   ├── validator.py     # Validation rules
│   ├── cli.py           # CLI interface
│   └── api.py           # REST API
├── tests/               # Test files
├── frontend/            # React UI
├── requirements.txt     # Python dependencies
└── START.txt            # Quick start guide
```

## Commands

| Command | Description |
|---------|-------------|
| `full-run` | Extract + validate in one step |
| `extract` | Extract data from PDFs only |
| `validate` | Validate JSON data only |

See START.txt for detailed instructions.
