INVOICE QC SERVICE - START GUIDE

IMPORTANT: First navigate to the project folder!
------------------------------------------------
    cd invoice-qc-service


STEP 1: INSTALL DEPENDENCIES (First time only)
----------------------------------------------
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt

(IF U HAVE THE FOLDER WITH INVOICE IN ALONG WITH THE FILE THEN FOLLOW THE STEP 2)
(IF NOT SKIP TO STEP 3)
STEP 2: RUN EXTRACTION + VALIDATION 
-----------------------------------
Basic run (single combined JSON file):
    .\venv\Scripts\python -m invoice_qc.cli full-run --pdf-dir pdfs --report validation_report.json

With SEPARATE JSON files for each invoice:
    .\venv\Scripts\python -m invoice_qc.cli full-run --pdf-dir pdfs --report validation_report.json --separate --output-dir output

This creates:
    output/
    ├── invoices/
    │   ├── AUFNR34343.json      <- Individual invoice file
    │   ├── AUFNR234953.json     <- Individual invoice file
    │   └── ...
    ├── all_invoices.json        <- Combined file with all invoices
    └── validation_report.json   <- Validation results


STEP 3: START THE API SERVER (IF U HAVE TO UPLOAD THE INVOICE)
----------------------------
    .\venv\Scripts\python -m uvicorn invoice_qc.api:app --reload

API Endpoints:
    http://localhost:8000/docs              <- Interactive API docs
    http://localhost:8000/health            <- Health check
    POST /extract-and-validate-pdfs         <- Upload PDFs, get JSON
    GET /invoices                           <- List saved invoices
    GET /download/{filename}                <- Download JSON file


STEP 4: START FRONTEND (Optional)
---------------------------------
    cd frontend
    npm install
    npm start

Frontend: http://localhost:3000


OUTPUT FILES


After running with --separate flag:
Check the folder name Output and in it the invoice folder have all the invoice 
in the seperate files or else the all_invoice.json file that is the main file that
contain all the invoices in it 

output/
├── invoices/                    <- Individual JSON files
│   ├── {invoice_number}.json
│   └── ...
├── all_invoices.json           <- All invoices combined
└── validation_report.json      <- Validation results

Each invoice JSON contains:
- invoice_number
- invoice_date
- seller_name, seller_address
- buyer_name, buyer_address
- currency, net_total, tax_amount, gross_total
- payment_terms
- line_items (description, quantity, unit_price, line_total)


  TROUBLESHOOTING

ERROR: "No module named 'invoice_qc'"
  -> Run: cd invoice-qc-service

ERROR: "scripts disabled on this system"
  -> Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

  
  CLI COMMANDS
  

Extract only:
    .\venv\Scripts\python -m invoice_qc.cli extract --pdf-dir pdfs --output extracted.json

Extract with separate files:
    .\venv\Scripts\python -m invoice_qc.cli extract --pdf-dir pdfs --output extracted.json --separate

Validate only:
    .\venv\Scripts\python -m invoice_qc.cli validate --input extracted.json --report report.json

Full pipeline with separate files:
    .\venv\Scripts\python -m invoice_qc.cli full-run --pdf-dir pdfs --report report.json --separate --output-dir output

Run tests:
    .\venv\Scripts\python -m pytest tests/ -v
