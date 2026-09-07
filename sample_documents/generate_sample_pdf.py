"""Script to generate a structured, multi-page sample PDF for RAG verification."""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak

OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "sample_knowledge.pdf"


def generate_pdf():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#4338ca"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("Acme Global AI Architecture & Data Policies", title_style))
    story.append(Paragraph("Document Version: 2026.2 | Classification: Confidential | Page 1", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=14))

    story.append(Paragraph("1. Executive Summary & System Overview", h2_style))
    story.append(Paragraph(
        "Acme Global operates an enterprise-grade AI knowledge platform designed to provide automated semantic "
        "search, multi-modal context retrieval, and zero-hallucination document synthesis. The system is deployed "
        "across distributed multi-region Kubernetes clusters with active-active redundancy.",
        body_style
    ))

    story.append(Paragraph("2. Data Retention and Lifecycle Policy", h2_style))
    story.append(Paragraph(
        "Customer data is retained for exactly 90 days following account deactivation. Once the 90-day grace "
        "period expires, all associated vector indexes, document chunks, and raw files are cryptographically erased "
        "using DoD 5220.22-M sanitation standards. Backup snapshots are permanently purged within 14 business days.",
        body_style
    ))

    story.append(Paragraph("3. Availability & SLA Commitments", h2_style))
    story.append(Paragraph(
        "Acme AI guarantees a 99.95% system uptime across all production regions. In the event of an unplanned "
        "outage exceeding 30 consecutive minutes, affected enterprise customers receive a 15% service credit on "
        "their monthly invoicing billing cycle.",
        body_style
    ))

    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("Security Protocols & Regulatory Compliance", title_style))
    story.append(Paragraph("Document Version: 2026.2 | Classification: Confidential | Page 2", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=14))

    story.append(Paragraph("4. Cryptographic Standards and Key Management", h2_style))
    story.append(Paragraph(
        "All customer data at rest is encrypted using AES-256-GCM with envelope encryption via AWS KMS or HashiCorp Vault. "
        "Data in transit requires TLS 1.3 with mandatory Perfect Forward Secrecy (PFS). Cipher suites that support "
        "CBC mode or RSA key exchanges are permanently disabled at the API gateway level.",
        body_style
    ))

    story.append(Paragraph("5. Compliance & External Audits", h2_style))
    story.append(Paragraph(
        "Acme Global undergoes annual third-party compliance verification. Certified compliance standards include:",
        body_style
    ))
    story.append(Paragraph("• <b>SOC 2 Type II:</b> Audited annually by Ernst & Young in Q3 covering security and confidentiality.", bullet_style))
    story.append(Paragraph("• <b>ISO 27001:2022:</b> Information security management system re-certified every 3 years.", bullet_style))
    story.append(Paragraph("• <b>HIPAA Omnibus Rule:</b> Business Associate Agreements (BAAs) supported for Healthcare Enterprise tiers.", bullet_style))
    story.append(Paragraph("• <b>GDPR & CCPA:</b> Full support for automated Right-to-be-Forgotten data deletion webhooks.", bullet_style))

    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("API Rate Limits & Vector Indexing Specifications", title_style))
    story.append(Paragraph("Document Version: 2026.2 | Classification: Confidential | Page 3", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=14))

    story.append(Paragraph("6. Enterprise Rate Limits and Quotas", h2_style))
    story.append(Paragraph(
        "Tier 1 Enterprise accounts are allocated 5,000 queries per minute (QPM) with a short-term burst allowance of up to "
        "7,500 QPM for intervals under 60 seconds. Requests exceeding these rate limits receive an HTTP 429 Too Many Requests "
        "status response containing a 'Retry-After' header indicating the cooldown period in seconds.",
        body_style
    ))

    story.append(Paragraph("7. Vector Store & Chunking Architecture", h2_style))
    story.append(Paragraph(
        "The RAG ingestion pipeline decomposes incoming documents using recursive character splitting with a target "
        "chunk size of 800 characters and a 150-character overlap window. Embeddings are generated using the 384-dimensional "
        "all-MiniLM-L6-v2 model or the 768-dimensional text-embedding-004 model. Vector indexing uses HNSW graphs with "
        "cosine distance metrics.",
        body_style
    ))

    doc.build(story)
    print(f"Generated sample PDF at: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_pdf()
