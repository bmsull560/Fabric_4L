"""Script to create sample PDF fixtures for testing.

Run this script to regenerate the sample PDFs if needed.
"""

from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def create_native_pdf(output_path: Path) -> None:
    """Create a digitally-born PDF with text and tables."""
    if not HAS_REPORTLAB:
        print("reportlab not installed. Install with: pip install reportlab")
        return

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph("Gartner Magic Quadrant Analysis", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Executive summary
    summary = Paragraph(
        "This analyst report provides strategic insights into the cloud infrastructure market. "
        "Leading vendors are evaluated based on completeness of vision and ability to execute.",
        styles['Normal']
    )
    story.append(summary)
    story.append(Spacer(1, 12))

    # Section header
    section = Paragraph("Market Leaders 2024", styles['Heading2'])
    story.append(section)
    story.append(Spacer(1, 6))

    # Table of vendors
    table_data = [
        ['Vendor', 'Vision Score', 'Execution Score', 'Quadrant'],
        ['AWS', '4.5', '4.8', 'Leader'],
        ['Microsoft Azure', '4.3', '4.6', 'Leader'],
        ['Google Cloud', '4.2', '4.1', 'Leader'],
        ['Oracle Cloud', '3.5', '3.8', 'Challenger'],
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # More content
    conclusion = Paragraph(
        "Forrester Wave and IDC MarketScape provide complementary perspectives. "
        "Organizations should evaluate solutions based on specific requirements including "
        "security, compliance, and integration capabilities.",
        styles['Normal']
    )
    story.append(conclusion)

    doc.build(story)
    print(f"Created native PDF: {output_path}")


def create_simple_text_pdf(output_path: Path) -> None:
    """Create a simple text-only PDF using basic canvas."""
    if not HAS_REPORTLAB:
        print("reportlab not installed. Install with: pip install reportlab")
        return

    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, "White Paper: Executive Summary")

    # Content
    c.setFont("Helvetica", 12)
    y = height - 108
    text_lines = [
        "This white paper examines the strategic implications of",
        "digital transformation initiatives in enterprise environments.",
        "",
        "Key findings include:",
        "- 75% of organizations have accelerated cloud adoption",
        "- ROI realization typically occurs within 18 months",
        "- Security remains the primary adoption barrier",
        "",
        "Recommendations for C-level executives are provided",
        "based on extensive research across Fortune 500 companies.",
    ]

    for line in text_lines:
        c.drawString(72, y, line)
        y -= 14

    c.save()
    print(f"Created simple text PDF: {output_path}")


def main():
    """Generate all sample PDF fixtures."""
    fixtures_dir = Path(__file__).parent

    # Create native PDF with tables
    native_pdf = fixtures_dir / "sample_native.pdf"
    create_native_pdf(native_pdf)

    # Create simple text PDF
    simple_pdf = fixtures_dir / "sample_simple.pdf"
    create_simple_text_pdf(simple_pdf)

    print("\nSample PDF fixtures created successfully!")
    print(f"Files created in: {fixtures_dir}")


if __name__ == "__main__":
    main()

