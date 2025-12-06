"""
Tests for validation module
"""
import pytest
from invoice_qc.models import Invoice, LineItem
from invoice_qc.validator import InvoiceValidator


def test_valid_invoice():
    """Test validation of a valid invoice"""
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date="2024-01-10",
        due_date="2024-01-25",
        seller_name="ACME Corp",
        seller_address="123 Main St",
        buyer_name="Client Inc",
        buyer_address="456 Oak Ave",
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert result.is_valid
    assert len(result.errors) == 0


def test_missing_required_fields():
    """Test validation fails for missing required fields"""
    invoice = Invoice(
        invoice_number="INV-002",
        # Missing invoice_date, seller_name, buyer_name
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any("invoice_date" in err.message for err in result.errors)


def test_tax_calculation_mismatch():
    """Test validation fails when tax calculation is wrong"""
    invoice = Invoice(
        invoice_number="INV-003",
        invoice_date="2024-01-10",
        seller_name="ACME Corp",
        buyer_name="Client Inc",
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=120.0,  # Should be 110.0
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert not result.is_valid
    assert any("tax_calculation" in err.rule for err in result.errors)


def test_invalid_currency():
    """Test validation fails for invalid currency"""
    invoice = Invoice(
        invoice_number="INV-004",
        invoice_date="2024-01-10",
        seller_name="ACME Corp",
        buyer_name="Client Inc",
        currency="XYZ",  # Invalid currency
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert not result.is_valid
    assert any("currency_validation" in err.rule for err in result.errors)


def test_due_date_before_invoice_date():
    """Test validation fails when due date is before invoice date"""
    invoice = Invoice(
        invoice_number="INV-005",
        invoice_date="2024-01-25",
        due_date="2024-01-10",  # Before invoice date
        seller_name="ACME Corp",
        buyer_name="Client Inc",
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert not result.is_valid
    assert any("due_date_logic" in err.rule for err in result.errors)


def test_line_items_sum_mismatch():
    """Test validation fails when line items don't sum to net total"""
    invoice = Invoice(
        invoice_number="INV-006",
        invoice_date="2024-01-10",
        seller_name="ACME Corp",
        buyer_name="Client Inc",
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
        line_items=[
            LineItem(description="Item 1", quantity=2, unit_price=20.0, line_total=40.0),
            LineItem(description="Item 2", quantity=1, unit_price=30.0, line_total=30.0),
            # Sum is 70.0, but net_total is 100.0
        ]
    )
    
    validator = InvoiceValidator()
    result = validator.validate_invoice(invoice)
    
    assert not result.is_valid
    assert any("line_items_sum" in err.rule for err in result.errors)


def test_duplicate_detection():
    """Test duplicate invoice detection"""
    invoice1 = Invoice(
        invoice_number="INV-007",
        invoice_date="2024-01-10",
        seller_name="ACME Corp",
        buyer_name="Client Inc",
        currency="USD",
        net_total=100.0,
        tax_amount=10.0,
        gross_total=110.0,
    )
    
    invoice2 = Invoice(
        invoice_number="INV-007",  # Same number
        invoice_date="2024-01-10",  # Same date
        seller_name="ACME Corp",  # Same seller
        buyer_name="Client Inc",
        currency="USD",
        net_total=200.0,
        tax_amount=20.0,
        gross_total=220.0,
    )
    
    validator = InvoiceValidator()
    report = validator.validate_invoices([invoice1, invoice2])
    
    # Second invoice should have duplicate error
    assert report.results[1].errors
    assert any("duplicate_invoice" in err.rule for err in report.results[1].errors)
