# src/parser.py
from config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB, DEBUG_MODE
from src.schemas import ParsedDocument, ExtractedTable, DocumentType
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent))


class DocumentParser:
    """
    Universal document parser using Docling.
    Handles PDF, Excel, DOCX, and images.
    """

    def __init__(self):
        print("Loading Docling converter... (first time may take 1-2 min)")
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.XLSX,
                InputFormat.IMAGE,
                InputFormat.HTML,
            ]
        )
        print("Docling ready.")

    def parse(self, file_path: str) -> ParsedDocument:
        """Parse any supported document and return structured output."""
        path = Path(file_path)

        if not path.exists():
            return ParsedDocument(
                source_file=file_path,
                error=f"File not found: {file_path}"
            )
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return ParsedDocument(
                source_file=file_path,
                error=f"Unsupported format: {path.suffix}"
            )
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            return ParsedDocument(
                source_file=file_path,
                error=f"File too large: {size_mb:.1f}MB. Max: {MAX_FILE_SIZE_MB}MB"
            )

        try:
            if DEBUG_MODE:
                print(f"Parsing: {path.name}")

            result = self.converter.convert(str(path))
            doc = result.document
            raw_text = doc.export_to_text()
            markdown = doc.export_to_markdown()
            tables = self._extract_tables(doc)
            doc_type = self._detect_document_type(path.name, raw_text)
            page_count = self._get_page_count(doc)

            if DEBUG_MODE:
                print(f"Parsed {path.name}: {len(raw_text)} chars, "
                      f"{len(tables)} tables, {page_count} pages")

            return ParsedDocument(
                source_file=str(path),
                document_type=doc_type,
                raw_text=raw_text,
                markdown=markdown,
                tables=tables,
                page_count=page_count
            )

        except Exception as e:
            print(f"Error parsing {path.name}: {e}")
            return ParsedDocument(source_file=file_path, error=str(e))

    def _extract_tables(self, doc) -> list:
        """Extract all tables from parsed document"""
        tables = []
        try:
            for i, table in enumerate(doc.tables):
                try:
                    df = table.export_to_dataframe()
                    if df.empty:
                        continue

                    # BUG FIX 6: df.values.tolist() passes float('nan') for empty
                    # cells which becomes the string "nan" in rows. This confuses
                    # keyword matching in extractors (e.g. "turnover nan" matches
                    # "turnover" but _parse_amount("nan") silently returns 0).
                    # Replace all nan/None with empty string before storing.
                    clean_rows = [
                        ['' if (str(cell) == 'nan' or cell is None) else str(cell)
                         for cell in row]
                        for row in df.values.tolist()
                    ]

                    extracted = ExtractedTable(
                        table_index=i,
                        headers=list(df.columns.astype(str)),
                        rows=clean_rows,
                        raw_text=df.to_string()
                    )
                    tables.append(extracted)

                except Exception as e:
                    if DEBUG_MODE:
                        print(f"Could not extract table {i}: {e}")
                    continue

        except Exception as e:
            if DEBUG_MODE:
                print(f"Table extraction error: {e}")

        return tables

    def _detect_document_type(self, filename: str, text: str) -> DocumentType:
        """Auto-detect document type from filename and content."""
        filename_lower = filename.lower()
        text_lower = text.lower()[:2000]

        if any(kw in filename_lower for kw in ["gst", "gstr", "3b", "2a", "r1"]):
            return DocumentType.GST_RETURN
        if any(kw in filename_lower for kw in ["itr", "income_tax", "incometax"]):
            return DocumentType.ITR
        if any(kw in filename_lower for kw in ["bank", "statement", "account"]):
            return DocumentType.BANK_STATEMENT
        if any(kw in filename_lower for kw in ["annual", "ar_", "annual_report"]):
            return DocumentType.ANNUAL_REPORT
        if any(kw in filename_lower for kw in ["balance", "p&l", "financial"]):
            return DocumentType.FINANCIAL_STATEMENT
        if any(kw in filename_lower for kw in ["legal", "notice", "court", "summon"]):
            return DocumentType.LEGAL_NOTICE

        if any(kw in text_lower for kw in ["gstin", "gstr", "igst", "cgst", "sgst"]):
            return DocumentType.GST_RETURN
        if any(kw in text_lower for kw in ["assessment year", "income tax return", "pan"]):
            return DocumentType.ITR
        if any(kw in text_lower for kw in ["account no", "debit", "credit", "balance"]):
            return DocumentType.BANK_STATEMENT
        if any(kw in text_lower for kw in ["directors report", "auditors report"]):
            return DocumentType.ANNUAL_REPORT

        return DocumentType.OTHER

    def _get_page_count(self, doc) -> int:
        try:
            return len(doc.pages) if hasattr(doc, 'pages') else 0
        except:
            return 0

    def parse_multiple(self, file_paths: list) -> list:
        results = []
        for i, path in enumerate(file_paths):
            print(f"Parsing file {i+1}/{len(file_paths)}: {Path(path).name}")
            results.append(self.parse(path))
        return results

    def get_summary(self, parsed: ParsedDocument) -> dict:
        return {
            "file": Path(parsed.source_file).name,
            "type": parsed.document_type.value,
            "pages": parsed.page_count,
            "tables": len(parsed.tables),
            "text_length": len(parsed.raw_text),
            "has_error": parsed.error is not None,
            "error": parsed.error
        }


if __name__ == "__main__":
    parser = DocumentParser()
    test_file = input(
        "Enter path to a PDF to test (or press Enter to skip): ").strip()
    if test_file and Path(test_file).exists():
        result = parser.parse(test_file)
        summary = parser.get_summary(result)
        print(f"\nFile:   {summary['file']}")
        print(f"Type:   {summary['type']}")
        print(f"Pages:  {summary['pages']}")
        print(f"Tables: {summary['tables']}")
        print(f"Text:   {summary['text_length']} characters")
        if result.error:
            print(f"Error:  {result.error}")
        else:
            print(f"\nFirst 500 chars:\n{result.raw_text[:500]}")
    else:
        print("No test file provided. Parser loaded successfully.")
