"""
Validation module - validates invoices against business rules
"""
from typing import List, Dict, Tuple
from datetime import datetime
from .models import (
    Invoice, ValidationError, InvoiceValidationResult,
    ValidationSummary, ValidationReport
)
from .utils import is_valid_currency, calculate_tolerance_match


class InvoiceValidator:
    """Validate invoices against schema and business rules"""
    
    def __init__(self, tolerance: float = 0.02, max_amount: float = 1000000):
        self.tolerance = tolerance
        self.max_amount = max_amount
        self.seen_invoices = set()
    
    def validate_invoices(self, invoices: List[Invoice]) -> ValidationReport:
        """Validate a list of invoices and return report"""
        results = []
        
        for invoice in invoices:
            result = self.validate_invoice(invoice)
            results.append(result)
        
        summary = self._create_summary(results)
        
        return ValidationReport(summary=summary, results=results)
    
    def validate_invoice(self, invoice: Invoice) -> InvoiceValidationResult:
        """Validate a single invoice"""
        invoice_id = invoice.invoice_number or "UNKNOWN"
        errors = []
        warnings = []
        
        # Run all validation rules
        errors.extend(self._check_completeness_rules(invoice))
        errors.extend(self._check_format_rules(invoice))
        errors.extend(self._check_business_rules(invoice))
        errors.extend(self._check_anomaly_rules(invoice))
        
        is_valid = len(errors) == 0
        
        return InvoiceValidationResult(
            invoice_id=invoice_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def _check_completeness_rules(self, invoice: Invoice) -> List[ValidationError]:
        """Check completeness rules"""
        errors = []
        
        # Rule 1: Required fields
        required_fields = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'seller_name': invoice.seller_name,
            'buyer_name': invoice.buyer_name,
        }
        
        for field, value in required_fields.items():
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    rule="required_field",
                    message=f"Missing required field: {field}"
                ))
        
        # Rule 2: Party information
        if invoice.seller_name:
            if not invoice.seller_address and not invoice.seller_tax_id:
                errors.append(ValidationError(
                    rule="party_information",
                    message="Seller must have address or tax ID"
                ))
        
        if invoice.buyer_name:
            if not invoice.buyer_address and not invoice.buyer_tax_id:
                errors.append(ValidationError(
                    rule="party_information",
                    message="Buyer must have address or tax ID"
                ))
        
        # Rule 3: Financial fields
        if invoice.net_total is None:
            errors.append(ValidationError(
                rule="financial_field",
                message="Missing net_total"
            ))
        
        if invoice.tax_amount is None:
            errors.append(ValidationError(
                rule="financial_field",
                message="Missing tax_amount"
            ))
        
        if invoice.gross_total is None:
            errors.append(ValidationError(
                rule="financial_field",
                message="Missing gross_total"
            ))
        
        # Rule 4: Currency specification
        if not invoice.currency or not invoice.currency.strip():
            errors.append(ValidationError(
                rule="currency_required",
                message="Currency must be specified"
            ))
        
        return errors
    
    def _check_format_rules(self, invoice: Invoice) -> List[ValidationError]:
        """Check type/format rules"""
        errors = []
        
        # Rule 5: Date format
        if invoice.invoice_date:
            if not self._is_valid_date(invoice.invoice_date):
                errors.append(ValidationError(
                    rule="date_format",
                    message=f"Invalid invoice_date format: {invoice.invoice_date}"
                ))
        
        if invoice.due_date:
            if not self._is_valid_date(invoice.due_date):
                errors.append(ValidationError(
                    rule="date_format",
                    message=f"Invalid due_date format: {invoice.due_date}"
                ))
        
        # Rule 6: Currency validation
        if invoice.currency:
            if not is_valid_currency(invoice.currency):
                errors.append(ValidationError(
                    rule="currency_validation",
                    message=f"Unknown currency: {invoice.currency}"
                ))
        
        # Rule 7: Numeric values
        if invoice.net_total is not None and invoice.net_total < 0:
            errors.append(ValidationError(
                rule="numeric_validation",
                message="net_total cannot be negative"
            ))
        
        if invoice.tax_amount is not None and invoice.tax_amount < 0:
            errors.append(ValidationError(
                rule="numeric_validation",
                message="tax_amount cannot be negative"
            ))
        
        if invoice.gross_total is not None and invoice.gross_total < 0:
            errors.append(ValidationError(
                rule="numeric_validation",
                message="gross_total cannot be negative"
            ))
        
        return errors
    
    def _check_business_rules(self, invoice: Invoice) -> List[ValidationError]:
        """Check business logic rules"""
        errors = []
        
        # Rule 8: Line items sum
        if invoice.line_items and invoice.net_total is not None:
            line_items_sum = sum(item.line_total for item in invoice.line_items)
            if not calculate_tolerance_match(line_items_sum, invoice.net_total, self.tolerance):
                errors.append(ValidationError(
                    rule="line_items_sum",
                    message=f"Line items sum ({line_items_sum:.2f}) doesn't match net_total ({invoice.net_total:.2f})"
                ))
        
        # Rule 9: Tax calculation
        if invoice.net_total is not None and invoice.tax_amount is not None and invoice.gross_total is not None:
            expected_gross = invoice.net_total + invoice.tax_amount
            if not calculate_tolerance_match(expected_gross, invoice.gross_total, self.tolerance):
                errors.append(ValidationError(
                    rule="tax_calculation",
                    message=f"net_total + tax_amount ({expected_gross:.2f}) doesn't match gross_total ({invoice.gross_total:.2f})"
                ))
        
        # Rule 10: Due date logic
        if invoice.invoice_date and invoice.due_date:
            try:
                inv_date = datetime.fromisoformat(invoice.invoice_date)
                due_date = datetime.fromisoformat(invoice.due_date)
                if due_date < inv_date:
                    errors.append(ValidationError(
                        rule="due_date_logic",
                        message=f"due_date ({invoice.due_date}) is before invoice_date ({invoice.invoice_date})"
                    ))
            except ValueError:
                pass  # Already caught in format rules
        
        return errors
    
    def _check_anomaly_rules(self, invoice: Invoice) -> List[ValidationError]:
        """Check for anomalies and duplicates"""
        errors = []
        
        # Rule 11: Duplicate detection
        invoice_key = (
            invoice.invoice_number,
            invoice.seller_name,
            invoice.invoice_date
        )
        
        if invoice_key in self.seen_invoices:
            errors.append(ValidationError(
                rule="duplicate_invoice",
                message=f"Duplicate invoice detected: {invoice.invoice_number}"
            ))
        else:
            self.seen_invoices.add(invoice_key)
        
        # Rule 12: Reasonable amounts
        if invoice.gross_total is not None:
            if invoice.gross_total <= 0:
                errors.append(ValidationError(
                    rule="reasonable_amount",
                    message="gross_total must be greater than 0"
                ))
            elif invoice.gross_total > self.max_amount:
                errors.append(ValidationError(
                    rule="reasonable_amount",
                    message=f"gross_total ({invoice.gross_total:.2f}) exceeds maximum ({self.max_amount:.2f})"
                ))
        
        return errors
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid ISO format"""
        try:
            datetime.fromisoformat(date_str)
            return True
        except (ValueError, TypeError):
            return False
    
    def _create_summary(self, results: List[InvoiceValidationResult]) -> ValidationSummary:
        """Create aggregated summary from validation results"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        error_counts = {}
        warning_counts = {}
        
        for result in results:
            for error in result.errors:
                key = f"{error.rule}: {error.message}"
                error_counts[key] = error_counts.get(key, 0) + 1
            
            for warning in result.warnings:
                key = f"{warning.rule}: {warning.message}"
                warning_counts[key] = warning_counts.get(key, 0) + 1
        
        return ValidationSummary(
            total_invoices=total,
            valid_invoices=valid,
            invalid_invoices=invalid,
            error_counts=error_counts,
            warning_counts=warning_counts
        )
