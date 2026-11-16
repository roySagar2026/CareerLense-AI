from __future__ import annotations

import json

from app.utils.html_text import extract_page, html_to_text


def test_strips_scripts_and_keeps_lists():
    html = (
        "<html><head><title>Backend Engineer - Acme</title><style>x{}</style></head><body>"
        "<script>alert(1)</script><nav>Menu</nav><h1>Backend Engineer</h1>"
        "<ul><li>Python</li><li>SQL</li></ul></body></html>"
    )
    text = html_to_text(html)
    assert "alert" not in text and "Menu" not in text
    assert "- Python" in text and "- SQL" in text
    assert extract_page(html).title == "Backend Engineer - Acme"


def test_prefers_json_ld_job_posting():
    posting = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Data Engineer",
        "description": "<p>Requirements</p><ul><li>SQL</li><li>Airflow</li></ul>",
        "hiringOrganization": {"@type": "Organization", "name": "Globex"},
        "jobLocation": {"address": {"addressLocality": "Pune", "addressCountry": "IN"}},
    }
    html = f'<html><body><div id="root"></div><script type="application/ld+json">{json.dumps(posting)}</script></body></html>'
    page = extract_page(html)
    assert page.title == "Data Engineer" and page.company == "Globex" and page.location == "Pune, IN"
    assert "- SQL" in page.text
