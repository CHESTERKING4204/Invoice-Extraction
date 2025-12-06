"""
FastAPI HTTP API for invoice validation
"""
import json
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List
import tempfile
from pathlib import Path

from .models import Invoice, ValidationReport
from .extractor import InvoiceExtractor
from .validator import InvoiceValidator

app = FastAPI(
    title="Invoice QC Service API",
    description="Extract and validate invoice data from PDFs",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory for saved files
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "invoice-qc-service"}


@app.post("/validate-json", response_model=ValidationReport)
async def validate_json(invoices: List[Invoice]):
    """
    Validate a list of invoice JSON objects
    """
    try:
        validator = InvoiceValidator()
        report = validator.validate_invoices(invoices)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(
    files: List[UploadFile] = File(...),
    save_separate: bool = False
):
    """
    Extract data from PDF files, validate them, and return JSON data
    
    - Extracts all invoice data
    - Validates against business rules
    - Returns extracted data + validation results
    - Optionally saves each invoice as separate JSON file
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files
            for file in files:
                if not file.filename.lower().endswith('.pdf'):
                    raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
                
                file_path = temp_path / file.filename
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
            
            # Extract invoices
            extractor = InvoiceExtractor()
            invoices = extractor.extract_from_directory(str(temp_path))
            
            # Convert to dict
            invoices_dict = [inv.model_dump() for inv in invoices]
            
            # Save to output directory
            invoices_dir = OUTPUT_DIR / "invoices"
            invoices_dir.mkdir(exist_ok=True)
            
            saved_files = []
            
            # Save each invoice as separate JSON
            for inv_dict in invoices_dict:
                inv_id = inv_dict.get("invoice_number", "unknown")
                filename = invoices_dir / f"{inv_id}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(inv_dict, f, indent=2, ensure_ascii=False)
                saved_files.append(str(filename))
            
            # Save combined file
            combined_file = OUTPUT_DIR / "all_invoices.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(invoices_dict, f, indent=2, ensure_ascii=False)
            
            # Validate invoices
            validator = InvoiceValidator()
            validation_report = validator.validate_invoices(invoices)
            
            # Save validation report
            report_file = OUTPUT_DIR / "validation_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(validation_report.model_dump(), f, indent=2, ensure_ascii=False)
            
            return {
                "message": "Processing complete",
                "total_invoices": len(invoices),
                "extracted_invoices": invoices_dict,
                "validation_report": validation_report.model_dump(),
                "saved_files": {
                    "individual_invoices": saved_files,
                    "combined_file": str(combined_file),
                    "validation_report": str(report_file)
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated JSON file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        # Check in invoices subdirectory
        file_path = OUTPUT_DIR / "invoices" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=filename, media_type="application/json")


@app.get("/invoices")
async def list_invoices():
    """List all extracted invoice JSON files"""
    invoices_dir = OUTPUT_DIR / "invoices"
    if not invoices_dir.exists():
        return {"invoices": []}
    
    files = list(invoices_dir.glob("*.json"))
    return {
        "invoices": [f.name for f in files],
        "count": len(files)
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Invoice QC Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "validate_json": "POST /validate-json",
            "extract_and_validate": "POST /extract-and-validate-pdfs",
            "list_invoices": "GET /invoices",
            "download": "GET /download/{filename}",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
