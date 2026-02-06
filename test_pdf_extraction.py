import io

from src.core.financial_report_analyzer import FinancialReportAnalyzer


def test_pdf_extraction():
    """Test PDF extraction with a simple test case"""

    # Create a minimal PDF content (this is a valid minimal PDF)
    minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"

    analyzer = FinancialReportAnalyzer()
    text = analyzer.extract_text_from_pdf(minimal_pdf)

    print("PDF extraction test passed. Extracted text:", repr(text))

    # Test error handling with invalid PDF
    invalid_pdf = b"This is not a valid PDF file"
    error_text = analyzer.extract_text_from_pdf(invalid_pdf)

    print("\nInvalid PDF test passed. Extracted text:", repr(error_text))


if __name__ == "__main__":
    test_pdf_extraction()
