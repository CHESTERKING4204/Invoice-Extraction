"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from invoice_qc.api import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validate_json_valid_invoice():
    """Test validation endpoint with valid invoice"""
    invoices = [
        {
            "invoice_number": "INV-001",
            "invoice_date": "2024-01-10",
            "due_date": "2024-01-25",
            "seller_name": "ACME Corp",
            "seller_address": "123 Main St",
            "buyer_name": "Client Inc",
            "buyer_address": "456 Oak Ave",
            "currency": "USD",
            "net_total": 100.0,
            "tax_amount": 10.0,
            "gross_total": 110.0,
            "line_items": []
        }
    ]
    
    response = client.post("/validate-json", json=invoices)
    assert response.status_code == 200
    
    data = response.json()
    assert data["summary"]["total_invoices"] == 1
    assert data["summary"]["valid_invoices"] == 1
    assert data["summary"]["invalid_invoices"] == 0


def test_validate_json_invalid_invoice():
    """Test validation endpoint with invalid invoice"""
    invoices = [
        {
            "invoice_number": "INV-002",
            # Missing required fields
            "currency": "USD",
            "net_total": 100.0,
            "tax_amount": 10.0,
            "gross_total": 110.0,
        }
    ]
    
    response = client.post("/validate-json", json=invoices)
    assert response.status_code == 200
    
    data = response.json()
    assert data["summary"]["total_invoices"] == 1
    assert data["summary"]["invalid_invoices"] == 1
    assert len(data["results"][0]["errors"]) > 0


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert "endpoints" in response.json()
