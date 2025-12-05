# AI Usage Notes - API Design

## Tool Used
ChatGPT-4 & GitHub Copilot

## Context
Designing FastAPI endpoints for invoice validation service.

## AI Suggestions

### Initial API Structure
**AI Suggested:**
```python
@app.post("/validate")
async def validate(data: dict):
    # validation logic
    return {"status": "ok"}
```

**Issue:** 
- No proper type validation
- Generic dict input
- No error handling
- No structured response

**My Implementation:**
```python
@app.post("/validate-json", response_model=ValidationReport)
async def validate_json(invoices: List[Invoice]):
    try:
        validator = InvoiceValidator()
        report = validator.validate_invoices(invoices)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
```

**Improvements:**
1. Used Pydantic models for type safety
2. Explicit response model
3. Proper error handling with HTTPException
4. Clear endpoint naming

---

### File Upload Endpoint
**AI Suggested:**
```python
@app.post("/upload")
async def upload(file: UploadFile):
    content = await file.read()
    # process file
```

**Issue:**
- Only handles single file
- No file type validation
- No temporary file cleanup
- Doesn't return structured data

**My Implementation:**
```python
@app.post("/extract-and-validate-pdfs", response_model=dict)
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save files, validate PDF extension
            # Extract and validate
            # Return both extracted data and validation results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
```

**Improvements:**
1. Multiple file support
2. PDF extension validation
3. Automatic cleanup with context manager
4. Returns both extraction and validation results
5. Proper exception hierarchy

---

### CORS Configuration
**AI Suggested:**
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

**My Addition:**
Added comment about production security:
```python
# In production, specify exact origins
allow_origins=["*"],  # Change to specific domains in production
```

**Rationale:** AI's suggestion works but isn't production-ready. Added documentation for future hardening.

---

## Key Learnings

1. **AI provides basic structure** but lacks production considerations
2. **Type safety matters** - Pydantic models catch errors early
3. **Error handling** needs to be explicit and hierarchical
4. **Resource cleanup** (temp files) must be handled properly
5. **Security considerations** (CORS, file validation) need manual review
