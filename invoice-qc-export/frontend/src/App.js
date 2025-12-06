import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [jsonInput, setJsonInput] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, valid, invalid

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setError(null);
  };

  const handleUploadPDFs = async () => {
    if (files.length === 0) {
      setError('Please select at least one PDF file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/extract-and-validate-pdfs`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResults(response.data.validation_report);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing PDFs');
    } finally {
      setLoading(false);
    }
  };

  const handleValidateJSON = async () => {
    if (!jsonInput.trim()) {
      setError('Please enter JSON data');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const invoices = JSON.parse(jsonInput);
      const response = await axios.post(`${API_BASE_URL}/validate-json`, invoices);
      setResults(response.data);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format');
      } else {
        setError(err.response?.data?.detail || 'Error validating JSON');
      }
    } finally {
      setLoading(false);
    }
  };

  const getFilteredResults = () => {
    if (!results || !results.results) return [];
    
    if (filter === 'valid') {
      return results.results.filter(r => r.is_valid);
    } else if (filter === 'invalid') {
      return results.results.filter(r => !r.is_valid);
    }
    return results.results;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📋 Invoice QC Console</h1>
        <p>Extract and validate invoice data</p>
      </header>

      <div className="container">
        <div className="input-section">
          <div className="upload-card">
            <h2>Upload PDFs</h2>
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileChange}
              className="file-input"
            />
            {files.length > 0 && (
              <p className="file-count">{files.length} file(s) selected</p>
            )}
            <button
              onClick={handleUploadPDFs}
              disabled={loading || files.length === 0}
              className="btn btn-primary"
            >
              {loading ? 'Processing...' : 'Upload & Validate'}
            </button>
          </div>

          <div className="json-card">
            <h2>Or Paste JSON</h2>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder='[{"invoice_number": "INV-001", ...}]'
              className="json-input"
              rows="8"
            />
            <button
              onClick={handleValidateJSON}
              disabled={loading || !jsonInput.trim()}
              className="btn btn-secondary"
            >
              {loading ? 'Validating...' : 'Validate JSON'}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {results && (
          <div className="results-section">
            <div className="summary-card">
              <h2>Validation Summary</h2>
              <div className="summary-stats">
                <div className="stat">
                  <span className="stat-label">Total</span>
                  <span className="stat-value">{results.summary.total_invoices}</span>
                </div>
                <div className="stat valid">
                  <span className="stat-label">Valid</span>
                  <span className="stat-value">{results.summary.valid_invoices}</span>
                </div>
                <div className="stat invalid">
                  <span className="stat-label">Invalid</span>
                  <span className="stat-value">{results.summary.invalid_invoices}</span>
                </div>
              </div>
            </div>

            <div className="results-table-container">
              <div className="table-header">
                <h2>Invoice Results</h2>
                <div className="filter-buttons">
                  <button
                    className={filter === 'all' ? 'active' : ''}
                    onClick={() => setFilter('all')}
                  >
                    All
                  </button>
                  <button
                    className={filter === 'valid' ? 'active' : ''}
                    onClick={() => setFilter('valid')}
                  >
                    Valid
                  </button>
                  <button
                    className={filter === 'invalid' ? 'active' : ''}
                    onClick={() => setFilter('invalid')}
                  >
                    Invalid
                  </button>
                </div>
              </div>

              <table className="results-table">
                <thead>
                  <tr>
                    <th>Invoice ID</th>
                    <th>Status</th>
                    <th>Errors</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {getFilteredResults().map((result, index) => (
                    <tr key={index}>
                      <td className="invoice-id">{result.invoice_id}</td>
                      <td>
                        <span className={`status-badge ${result.is_valid ? 'valid' : 'invalid'}`}>
                          {result.is_valid ? '✓ Valid' : '✗ Invalid'}
                        </span>
                      </td>
                      <td className="error-count">{result.errors.length}</td>
                      <td>
                        {result.errors.length > 0 && (
                          <ul className="error-list">
                            {result.errors.map((err, i) => (
                              <li key={i}>
                                <strong>{err.rule}:</strong> {err.message}
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
