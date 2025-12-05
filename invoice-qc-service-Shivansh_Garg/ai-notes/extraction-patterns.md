# AI Usage Notes - Extraction Patterns

## Tool Used
ChatGPT-4

## Context
Needed regex patterns to extract various invoice fields from PDF text.

## AI Suggestions

### Invoice Number Pattern
**AI Suggested:**
```python
r"Invoice\s*(?:No|Number|#)[:\s]*(\S+)"
```

**Issue:** Didn't handle variations like "Invoice ID", "Invoice No." (with period), or invoice numbers with hyphens properly.

**My Modified Version:**
```python
r"Invoice\s*(?:No\.?|Number|#|ID)[:\s]*([A-Z0-9-]+)"
```

**Rationale:** Added optional period after "No", included "ID" variant, and specified character class for invoice numbers to avoid capturing extra text.

---

### Date Extraction
**AI Suggested:**
```python
r"Date[:\s]*([\d/.-]+)"
```

**Issue:** Too generic - would match any date in the document, not specifically invoice date.

**My Modified Version:**
```python
[
    r"Invoice\s*Date[:\s]*([\d/.-]+)",
    r"Date[:\s]*([\d/.-]+)",
    r"Issued[:\s]*([\d/.-]+)",
]
```

**Rationale:** Created priority list with "Invoice Date" first, then generic "Date", then "Issued" as fallback.

---

### Amount Extraction
**AI Suggested:**
```python
r"Total[:\s]*([\d,\.]+)"
```

**Issue:** Didn't handle European number format (1.234,56) vs US format (1,234.56), and didn't remove currency symbols.

**My Implementation:**
Created a dedicated `extract_amount()` function that:
1. Removes currency symbols
2. Detects format based on comma/period positions
3. Normalizes to float

This was more robust than a single regex pattern.

---

## Key Learnings

1. **AI is good for starting points** but needs domain-specific refinement
2. **Real-world data is messier** than AI assumes
3. **Multiple patterns with priority** work better than one "perfect" regex
4. **Helper functions** are often better than complex regex for parsing
