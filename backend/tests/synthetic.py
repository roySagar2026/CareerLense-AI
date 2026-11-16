"""Synthetic (fictional) resume and job fixtures. Never use real candidate documents."""

from __future__ import annotations

import io

RESUME_BLOCKS: list[tuple[str, str]] = [
    ("name", "Asha Verma"),
    ("plain", "asha.verma@example.com | +91 98765 43210 | github.com/asha-demo"),
    ("heading", "PROFESSIONAL SUMMARY"),
    ("plain", "Backend developer with 3 years of experience building Python services and data reports."),
    ("heading", "TECHNICAL SKILLS"),
    ("plain", "Languages: Python, C++, SQL, JavaScript"),
    ("plain", "Frameworks: Flask, React"),
    ("plain", "Databases: PostgreSQL, Redis"),
    ("plain", "Tools: Git, Linux"),
    ("heading", "EXPERIENCE"),
    ("plain", "Software Engineer, Northwind Labs    Jan 2022 - Present"),
    ("bullet", "Built REST APIs in Python and Flask serving 20,000 daily requests"),
    ("bullet", "Optimized PostgreSQL queries, reducing report latency by 40%"),
    ("bullet", "Implemented unit tests with pytest covering 85% of services"),
    ("plain", "Junior Developer, Acme Systems    Jun 2020 - Dec 2021"),
    ("bullet", "Developed internal dashboards using React and JavaScript"),
    ("bullet", "Wrote SQL reports for the finance team"),
    ("heading", "PROJECTS"),
    ("plain", "Inventory Tracker | Personal project"),
    ("bullet", "Designed a stock management web app with Flask and PostgreSQL"),
    ("plain", "Tech: Python, Flask, PostgreSQL, Redis"),
    ("heading", "EDUCATION"),
    ("plain", "B.Tech in Computer Science, Example Institute of Technology, 2020"),
    ("heading", "CERTIFICATIONS"),
    ("plain", "AWS Certified Cloud Practitioner"),
]

JOB_TEXT = """Backend Engineer

About us
We are a fintech startup building payment tools.

Responsibilities
- Design and build REST APIs in Python for our payment platform
- Deploy services using Docker and Kubernetes on AWS
- Write unit tests and review code from teammates

Requirements
- 3+ years of experience in backend development
- Strong Python and SQL skills
- Experience with Django or FastAPI
- Hands-on experience with PostgreSQL
- Bachelor's degree in Computer Science or equivalent

Nice to have
- Terraform
- AWS Certified Solutions Architect
"""


def make_docx(blocks: list[tuple[str, str]] = RESUME_BLOCKS) -> bytes:
    from docx import Document

    doc = Document()
    for kind, text in blocks:
        if kind == "bullet":
            doc.add_paragraph(text, style="List Bullet")
        elif kind in {"heading", "name"}:
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(text)
            run.bold = True
        else:
            doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def make_pdf(blocks: list[tuple[str, str]] = RESUME_BLOCKS) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4
    y = height - 60
    for kind, text in blocks:
        if kind in {"heading", "name"}:
            pdf.setFont("Helvetica-Bold", 14 if kind == "heading" else 18)
            y -= 8
        else:
            pdf.setFont("Helvetica", 10)
        shown = f"• {text}" if kind == "bullet" else text
        pdf.drawString(50, y, shown)
        y -= 18
    pdf.save()
    return buffer.getvalue()
