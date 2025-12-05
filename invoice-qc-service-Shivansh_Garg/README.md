# Invoice QC Service

A comprehensive Invoice Extraction & Quality Control Service that extracts structured data from PDF invoices and validates them against business rules.

## Overview

This project implements:
- ✅ **PDF Extraction Module**: Extracts structured data from invoice PDFs
- ✅ **Validation Core**: Validates invoices against schema and business rules
- ✅ **CLI Tool**: Command-line interface for extraction and validation
- ✅ **HTTP API**: FastAPI-based REST API for integration
- ✅ **Frontend UI (Bonus)**: React-based QC console for invoice review

---

## Schema & Validation Design

### Invoice Schema Fields

#### Core Invoice-Level Fields (12 fields):

1. **invoice_number** (string): Unique identifier for the invoice
2. **invoice_date** (string, ISO format): Date when invoice was issued
3. **due_date** (string, ISO format): Payment due date
4. **seller_name** (string): Name of the selling company
5. **seller_address** (string): Seller's business address
6. **seller_tax_id** (string): Seller's VAT/Tax ID
7. **buyer_name** (string): Name of the buying company
8. **buyer_address** (string): Buyer's business address
9. **buyer_tax_id** (string): Buyer's VAT/Tax ID
10. **currency** (string): Currency code (EUR, USD, INR, etc.)
11. **net_total** (float): Total amount before tax
12. **tax_amount** (float): Total tax amount
13. **gross_total** (float): Final amount including tax
14. **payment_terms** (string): Payment terms description
15. **external_reference** (string, optional): PO number or external reference

#### Line Items Structure:
Each invoice can contain multiple line items with:
- **description** (string): Product/service description
- **quantity** (float): Number of units
- **unit_price** (float): Price per unit
- **line_total** (float): Total for this line (quantity × unit_price)

### Validation Rules

#### Completeness Rules (4 rules):
1. **Required Fields**: `invoice_number`, `invoice_date`, `seller_name`, `buyer_name` must be non-empty
   - *Rationale*: These are essential for identifying and processing any invoice
2. **Party Information**: Both seller and buyer must have at least name and one of (address or tax_id)
   - *Rationale*: Ensures we can identify the parties involved in the transaction
3. **Financial Fields**: `net_total`, `tax_amount`, `gross_total` must be present
   - *Rationale*: Core financial data needed for accounting and payment processing
4. **Currency Specification**: Currency must be specified and non-empty
   - *Rationale*: Essential for multi-currency operations and accounting

#### Type/Format Rules (3 rules):
5. **Date Format**: All dates must be valid ISO format (YYYY-MM-DD) or parseable date strings
   - *Rationale*: Ensures consistent date handling across systems
6. **Currency Validation**: Currency must be in known set (EUR, USD, GBP, INR, JPY, CHF, etc.)
   - *Rationale*: Prevents typos and ensures compatibility with financial systems
7. **Numeric Values**: All monetary amounts must be valid numbers (not negative for totals)
   - *Rationale*: Prevents data corruption and invalid financial records

#### Business Rules (3 rules):
8. **Line Items Sum**: Sum of line item totals should match net_total (within 0.02 tolerance)
   - *Rationale*: Detects calculation errors or data extraction issues
9. **Tax Calculation**: net_total + tax_amount should equal gross_total (within 0.02 tolerance)
   - *Rationale*: Ensures invoice arithmetic is correct
10. **Due Date Logic**: due_date must be on or after invoice_date
    - *Rationale*: Payment cannot be due before invoice is issued

#### Anomaly/Duplicate Rules (2 rules):
11. **Duplicate Detection**: No duplicate invoices (same invoice_number + seller_name + invoice_date)
    - *Rationale*: Prevents double-processing and payment errors
12. **Reasonable Amounts**: Gross total should be > 0 and < 1,000,000 (configurable threshold)
    - *Rationale*: Flags potential data extraction errors or fraudulent invoices

---

## Architecture

### Folder Structure
```
invoice-qc-service/
├── invoice_qc/
│   ├── __init__.py
│   ├── extractor.py       # PDF extraction logic
│   ├── validator.py       # Validation rules engine
│   ├── cli.py            # CLI interface
│   ├── api.py            # FastAPI application
│   ├── models.py         # Pydantic models
│   └── utils.py          # Helper functions
├── frontend/             # React QC console
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── ...
├── pdfs/                 # Sample invoice PDFs (add here)
├── ai-notes/            # AI usage documentation
├── requirements.txt
├── .env.example
└── README.md
```

### System Flow

```
┌─────────────┐
│  PDF Files  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Extractor Module   │  ← pdfplumber + regex patterns
│  (extractor.py)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Structured JSON    │  ← Invoice schema
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Validator Module   │  ← Business rules
│  (validator.py)     │
└──────┬──────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│  CLI Tool   │    │  HTTP API   │   │  Frontend   │
│  (cli.py)   │    │  (api.py)   │   │   (React)   │
└─────────────┘    └─────────────┘   └─────────────┘
```

### Component Details

**Extractor Pipeline**:
- Uses `pdfplumber` for text extraction
- Pattern-based field extraction with regex
- Handles table detection for line items
- Fallback strategies for missing fields

**Validation Core**:
- Rule-based validation engine
- Per-invoice error tracking
- Aggregated summary statistics
- Extensible rule system

**CLI**:
- Three modes: extract, validate, full-run
- JSON input/output
- Human-readable summaries
- Exit codes for CI/CD integration

**API**:
- FastAPI with automatic OpenAPI docs
- Endpoints: /validate-json, /extract-and-validate-pdfs, /health
- CORS enabled for frontend integration
- Structured error responses

**Frontend (Bonus)**:
- React-based single-page app
- Upload PDFs or paste JSON
- Real-time validation via API
- Filter/sort by validation status

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)

### Backend Setup

1. **Create virtual environment**:
```bash
cd invoice-qc-service
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Environment configuration** (optional):
```bash
cp .env.example .env
# Edit .env if needed
```

### Frontend Setup (Optional)

```bash
cd frontend
npm install
```

---

## Usage

### CLI Commands

#### 1. Extract Only
```bash
python -m invoice_qc.cli extract --pdf-dir pdfs --output extracted_invoices.json
```

#### 2. Validate Only
```bash
python -m invoice_qc.cli validate --input extracted_invoices.json --report validation_report.json
```

#### 3. Full Run (Extract + Validate)
```bash
python -m invoice_qc.cli full-run --pdf-dir pdfs --report validation_report.json
```

### HTTP API

#### Start the API server:
```bash
uvicorn invoice_qc.api:app --reload --port 8000
```

#### Example API Calls:

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Validate JSON**:
```bash
curl -X POST http://localhost:8000/validate-json \
  -H "Content-Type: application/json" \
  -d @extracted_invoices.json
```

**Extract and Validate PDFs**:
```bash
curl -X POST http://localhost:8000/extract-and-validate-pdfs \
  -F "files=@pdfs/invoice1.pdf" \
  -F "files=@pdfs/invoice2.pdf"
```

**API Documentation**: Visit `http://localhost:8000/docs` for interactive Swagger UI

### Frontend (Bonus)

```bash
cd frontend
npm start
# Opens at http://localhost:3000
```

Features:
- Upload multiple PDFs
- Paste JSON for validation
- View validation results in table
- Filter by valid/invalid status
- Color-coded error badges

---

## AI Usage Notes

### Tools Used
- **ChatGPT-4**: Used for initial project structure planning, regex pattern suggestions, and FastAPI boilerplate
- **GitHub Copilot**: Used for code completion, especially in repetitive validation rules and test cases

### Specific Use Cases

1. **PDF Extraction Patterns**: Asked AI for regex patterns to extract invoice numbers, dates, and amounts
   - AI suggested: `r"Invoice\s*(?:No|Number|#)[:\s]*(\S+)"`
   - Modified to handle more variations: `r"Invoice\s*(?:No\.?|Number|#|ID)[:\s]*([A-Z0-9-]+)"`

2. **FastAPI Structure**: Used AI to generate initial API endpoint structure
   - AI suggestion was good but lacked proper error handling
   - Added custom exception handlers and validation error responses

3. **Line Item Table Parsing**: AI suggested using `pdfplumber.extract_table()`
   - **Issue**: AI's approach assumed perfect table structure, which failed on real PDFs
   - **My fix**: Implemented fallback text-based parsing with position detection

4. **Validation Rule Engine**: AI suggested using decorators for rules
   - **Issue**: Made it harder to track which rules failed
   - **My approach**: Used explicit rule functions with clear return values (rule_name, passed, message)

### AI Chat Exports
See `/ai-notes/` folder for:
- `extraction-patterns.md`: Regex pattern discussions
- `api-design.md`: FastAPI structure conversations
- `validation-logic.md`: Rule engine design iterations

---

## Assumptions & Limitations

### Assumptions
1. **PDF Format**: Invoices are text-based PDFs (not scanned images)
2. **Language**: Invoices are primarily in English
3. **Structure**: Invoices follow common B2B format with clear labels
4. **Currency**: Single currency per invoice
5. **Line Items**: Line items appear in table-like format

### Known Limitations
1. **OCR**: No OCR support for scanned/image PDFs (would need pytesseract)
2. **Multi-page**: Limited testing on multi-page invoices
3. **Languages**: Non-English invoices may have lower extraction accuracy
4. **Complex Tables**: Nested or merged table cells may not parse correctly
5. **Handwritten**: Cannot process handwritten amounts or notes
6. **Performance**: Not optimized for batch processing 1000+ invoices (would need async/queue)

### Edge Cases Not Handled
- Invoices with multiple tax rates per line item
- Credit notes (negative invoices)
- Partial payments or installments
- Non-standard date formats (e.g., "1st January 2024")
- Currency symbols without codes (e.g., $ without USD)

---

## Integration into Larger Systems

### API Integration
Other services can integrate by:
```python
import requests

# After document processing pipeline
response = requests.post(
    "http://invoice-qc-service:8000/extract-and-validate-pdfs",
    files={"files": open("invoice.pdf", "rb")}
)
validation_results = response.json()
```

### Queue/Event-Driven Architecture
```
Document Upload → S3 → Lambda/SQS → Invoice QC Service → Results DB → Dashboard
```

### Containerization
```dockerfile
# Dockerfile included in project
docker build -t invoice-qc-service .
docker run -p 8000:8000 invoice-qc-service
```

### Future Enhancements
- **Database**: Store validation history (PostgreSQL/MongoDB)
- **Queue**: Process invoices asynchronously (Celery + Redis)
- **ML**: Train model for better field extraction
- **Webhooks**: Notify external systems on validation completion
- **Audit Log**: Track all validation events for compliance

---

## Video Demonstration

🎥 **Video Link**: [Add your Google Drive link here]

*(Make sure sharing is set to "Anyone with Link")*

---

## Testing

Run tests:
```bash
pytest tests/ -v
```

---

## License

MIT License

---

## Contact

For questions or issues, please contact [Your Name] at [Your Email]
