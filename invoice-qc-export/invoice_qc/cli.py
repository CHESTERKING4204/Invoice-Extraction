"""
CLI interface for invoice extraction and validation
"""
import json
import sys
import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .extractor import InvoiceExtractor
from .validator import InvoiceValidator
from .models import Invoice

app = typer.Typer(help="Invoice QC Service - Extract and validate invoices")
console = Console()


@app.command()
def extract(
    pdf_dir: str = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    output: str = typer.Option(..., "--output", help="Output JSON file path"),
    separate: bool = typer.Option(False, "--separate", help="Save each invoice as separate JSON file")
):
    """
    Extract structured data from PDF invoices
    """
    console.print(f"[bold blue]Extracting invoices from:[/bold blue] {pdf_dir}")
    
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    
    console.print(f"[green]✓[/green] Extracted {len(invoices)} invoices")
    
    # Convert to dict for JSON serialization
    invoices_dict = [inv.model_dump() for inv in invoices]
    
    if separate:
        # Save each invoice as separate file
        output_dir = Path(output).parent / "invoices_json"
        output_dir.mkdir(exist_ok=True)
        
        for inv_dict in invoices_dict:
            inv_id = inv_dict.get("invoice_number", "unknown")
            filename = output_dir / f"{inv_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(inv_dict, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓[/green] Saved: {filename}")
        
        console.print(f"[green]✓[/green] All invoices saved to: {output_dir}")
    else:
        # Save all to single file
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(invoices_dict, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓[/green] Saved to: {output}")


@app.command()
def validate(
    input: str = typer.Option(..., "--input", help="Input JSON file with extracted invoices"),
    report: str = typer.Option(..., "--report", help="Output validation report JSON file")
):
    """
    Validate extracted invoices against business rules
    """
    console.print(f"[bold blue]Validating invoices from:[/bold blue] {input}")
    
    # Load invoices
    with open(input, 'r') as f:
        invoices_data = json.load(f)
    
    invoices = [Invoice(**inv) for inv in invoices_data]
    
    # Validate
    validator = InvoiceValidator()
    validation_report = validator.validate_invoices(invoices)
    
    # Print summary
    _print_summary(validation_report)
    
    # Save report
    with open(report, 'w') as f:
        json.dump(validation_report.model_dump(), f, indent=2)
    
    console.print(f"\n[green]✓[/green] Report saved to: {report}")
    
    # Exit with error code if there are invalid invoices
    if validation_report.summary.invalid_invoices > 0:
        sys.exit(1)


@app.command()
def full_run(
    pdf_dir: str = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    report: str = typer.Option(..., "--report", help="Output validation report JSON file"),
    save_extracted: Optional[str] = typer.Option(None, "--save-extracted", help="Save extracted data to JSON file"),
    separate: bool = typer.Option(False, "--separate", help="Save each invoice as separate JSON file"),
    output_dir: str = typer.Option("output", "--output-dir", help="Output directory for JSON files")
):
    """
    Extract and validate invoices in one step (end-to-end)
    """
    console.print("[bold blue]Running full invoice QC pipeline[/bold blue]\n")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Step 1: Extract
    console.print("[bold]Step 1: Extraction[/bold]")
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    console.print(f"[green]✓[/green] Extracted {len(invoices)} invoices\n")
    
    # Convert to dict
    invoices_dict = [inv.model_dump() for inv in invoices]
    
    # Save extracted data
    if separate:
        # Save each invoice as separate JSON file
        invoices_dir = output_path / "invoices"
        invoices_dir.mkdir(exist_ok=True)
        
        console.print("[bold]Saving individual invoice files:[/bold]")
        for inv_dict in invoices_dict:
            inv_id = inv_dict.get("invoice_number", "unknown")
            filename = invoices_dir / f"{inv_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(inv_dict, f, indent=2, ensure_ascii=False)
            console.print(f"  [green]✓[/green] {filename}")
        console.print(f"[green]✓[/green] All invoices saved to: {invoices_dir}\n")
    
    # Always save combined file
    combined_file = output_path / "all_invoices.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(invoices_dict, f, indent=2, ensure_ascii=False)
    console.print(f"[green]✓[/green] Combined data saved to: {combined_file}\n")
    
    # Step 2: Validate
    console.print("[bold]Step 2: Validation[/bold]")
    validator = InvoiceValidator()
    validation_report = validator.validate_invoices(invoices)
    
    # Print summary
    _print_summary(validation_report)
    
    # Save validation report
    report_file = output_path / report if not Path(report).is_absolute() else Path(report)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report.model_dump(), f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]✓[/green] Validation report saved to: {report_file}")
    
    # Exit with error code if there are invalid invoices
    if validation_report.summary.invalid_invoices > 0:
        sys.exit(1)


def _print_summary(report):
    """Print validation summary in a nice format"""
    summary = report.summary
    
    console.print("\n[bold]Validation Summary[/bold]")
    console.print(f"Total Invoices: {summary.total_invoices}")
    console.print(f"[green]Valid: {summary.valid_invoices}[/green]")
    console.print(f"[red]Invalid: {summary.invalid_invoices}[/red]")
    
    if summary.error_counts:
        console.print("\n[bold red]Top Errors:[/bold red]")
        sorted_errors = sorted(summary.error_counts.items(), key=lambda x: x[1], reverse=True)
        for error, count in sorted_errors[:5]:
            console.print(f"  • {error}: [red]{count}[/red]")
    
    # Print detailed results table
    if report.results:
        console.print("\n[bold]Detailed Results:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Invoice ID", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Errors", justify="right")
        
        for result in report.results:
            status = "[green]✓ Valid[/green]" if result.is_valid else "[red]✗ Invalid[/red]"
            error_count = str(len(result.errors))
            table.add_row(result.invoice_id, status, error_count)
        
        console.print(table)


if __name__ == "__main__":
    app()
