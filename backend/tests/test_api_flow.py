from __future__ import annotations

import uuid

from tests.conftest import auth_headers, create_job, register, upload_resume

PDF_MIME = "application/pdf"


def test_full_journey(client):
    headers = auth_headers(client)

    resume = upload_resume(client, headers)
    assert resume.status_code == 201, resume.text
    detail = resume.json()
    assert detail["status"] == "ready" and detail["extraction_method"] == "docx"
    assert {s["section_type"] for s in detail["sections"]} >= {"skills", "experience", "education"}
    assert any(s["canonical_name"] == "Python" and s["evidence_level"] == "demonstrated" for s in detail["skills"])
    assert detail["parsed_data"]["contact"]["email"] == "asha.verma@example.com"

    job = create_job(client, headers)
    assert job.status_code == 201, job.text
    assert job.json()["requirements_count"] > 5

    created = client.post(
        "/api/v1/analysis", json={"resume_id": detail["id"], "job_id": job.json()["id"]}, headers=headers
    )
    assert created.status_code == 201, created.text
    analysis = created.json()
    assert 0 <= analysis["overall_score"] <= 100
    assert "NOT the score" in analysis["disclaimer"]
    assert set(analysis["dimension_scores"]) == {
        "required_skills",
        "preferred_skills",
        "experience",
        "responsibilities",
        "education",
        "structure",
    }

    keywords = client.get(
        f"/api/v1/analysis/{analysis['id']}/keywords?result_category=missing_mandatory", headers=headers
    )
    assert keywords.status_code == 200
    missing = {k["normalized_keyword"] for k in keywords.json()["items"]}
    assert "Docker" in missing

    semantic = client.get(
        f"/api/v1/analysis/{analysis['id']}/keywords?result_category=semantic", headers=headers
    ).json()
    assert all(k["credit"] <= 0.8 for k in semantic["items"])
    searched = client.get(f"/api/v1/analysis/{analysis['id']}/keywords?search=postgres", headers=headers).json()
    assert searched["total"] >= 1

    recs = client.get(f"/api/v1/analysis/{analysis['id']}/recommendations", headers=headers).json()
    assert recs and all(r["is_suggestion"] for r in recs)
    assert any(r["kind"] == "add_keyword" and r["caveat"] for r in recs)

    # History, filters, compare, trend, dashboard
    listing = client.get("/api/v1/analysis?company=north", headers=headers).json()
    assert listing["total"] == 1
    second = upload_resume(client, headers, parent=detail["id"])
    assert second.json()["version"] == 2
    again = client.post(
        "/api/v1/analysis", json={"resume_id": second.json()["id"], "job_id": job.json()["id"]}, headers=headers
    ).json()
    comparison = client.get(f"/api/v1/analysis/compare?a={analysis['id']}&b={again['id']}", headers=headers)
    assert comparison.status_code == 200 and "score_delta" in comparison.json()
    trend = client.get(f"/api/v1/analysis/trend?job_id={job.json()['id']}", headers=headers).json()
    assert [p["resume_version"] for p in trend] == [1, 2]
    versions = client.get(f"/api/v1/resumes/{detail['id']}/versions", headers=headers).json()
    assert [v["version"] for v in versions] == [1, 2]

    summary = client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert summary["total_resumes"] == 2 and summary["total_analyses"] == 2
    assert summary["average_score"] is not None and summary["best_resume"]
    activity = client.get("/api/v1/dashboard/recent-activity", headers=headers).json()
    assert any("Analyzed" in a["label"] for a in activity)

    # Deleting a resume cascades to its analyses
    assert client.delete(f"/api/v1/resumes/{detail['id']}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/analysis/{analysis['id']}", headers=headers).status_code == 404
    assert client.get("/api/v1/analysis", headers=headers).json()["total"] == 1


def test_section_correction_recomputes_skills(client):
    headers = auth_headers(client)
    resume = upload_resume(client, headers).json()
    skills_section = next(s for s in resume["sections"] if s["section_type"] == "skills")
    updated = client.patch(
        f"/api/v1/resumes/{resume['id']}/sections/{skills_section['id']}",
        json={"content": "Languages: Python, Rust, Go"},
        headers=headers,
    )
    assert updated.status_code == 200
    names = {s["canonical_name"] for s in updated.json()["skills"]}
    assert {"Rust", "Go"} <= names and "C++" not in names
    assert next(s for s in updated.json()["sections"] if s["id"] == skills_section["id"])["user_edited"] is True

    reprocessed = client.post(f"/api/v1/resumes/{resume['id']}/reprocess", headers=headers).json()
    assert "C++" in {s["canonical_name"] for s in reprocessed["skills"]}  # manual edits discarded


def test_original_file_is_private_and_streams(client):
    headers = auth_headers(client)
    resume = upload_resume(client, headers).json()
    assert client.get(f"/api/v1/resumes/{resume['id']}/file").status_code == 401
    ok = client.get(f"/api/v1/resumes/{resume['id']}/file", headers=headers)
    assert ok.status_code == 200 and ok.content[:2] == b"PK"


def test_user_isolation(client):
    a = auth_headers(client, "a@example.com")
    b_token = register(client, "b@example.com")["access_token"]
    b = {"Authorization": f"Bearer {b_token}"}

    resume = upload_resume(client, a).json()
    job = create_job(client, a).json()
    analysis = client.post("/api/v1/analysis", json={"resume_id": resume["id"], "job_id": job["id"]}, headers=a).json()

    for path in (
        f"/api/v1/resumes/{resume['id']}",
        f"/api/v1/resumes/{resume['id']}/file",
        f"/api/v1/resumes/{resume['id']}/versions",
        f"/api/v1/jobs/{job['id']}",
        f"/api/v1/analysis/{analysis['id']}",
        f"/api/v1/analysis/{analysis['id']}/keywords",
        f"/api/v1/analysis/{analysis['id']}/recommendations",
        f"/api/v1/analysis/trend?job_id={job['id']}",
    ):
        assert client.get(path, headers=b).status_code == 404, path
    assert client.delete(f"/api/v1/resumes/{resume['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/jobs/{job['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/analysis/{analysis['id']}", headers=b).status_code == 404
    assert (
        client.post("/api/v1/analysis", json={"resume_id": resume["id"], "job_id": job["id"]}, headers=b).status_code
        == 404
    )
    assert client.get("/api/v1/resumes", headers=b).json()["total"] == 0
    assert client.get("/api/v1/analysis", headers=b).json()["total"] == 0
    # Nonexistent id behaves identically to someone else's id
    assert client.get(f"/api/v1/resumes/{uuid.uuid4()}", headers=a).status_code == 404


def test_upload_security(client):
    headers = auth_headers(client)

    def post(name: str, content: bytes, mime: str = PDF_MIME):
        return client.post("/api/v1/resumes/upload", files={"file": (name, content, mime)}, headers=headers)

    assert post("evil.exe", b"MZ\x90\x00").status_code == 415
    assert post("fake.pdf", b"this is not a pdf").status_code == 415
    assert post("fake.docx", b"PK\x03\x04 not really a docx").status_code == 415
    assert post("empty.pdf", b"").status_code == 422
    assert post("big.pdf", b"%PDF-1.4\n" + b"0" * (5 * 1024 * 1024)).status_code == 413
    traversal = post("../../etc/passwd.pdf", b"%PDF-1.4 broken")
    assert traversal.status_code == 201  # accepted as a (failed) parse, but the name is sanitised
    assert "/" not in traversal.json()["original_filename"] and traversal.json()["status"] == "failed"
    assert traversal.json()["error_message"]


def test_job_validation_and_url_import_blocks_internal_targets(client):
    headers = auth_headers(client)
    assert client.post("/api/v1/jobs", json={"raw_text": "too short"}, headers=headers).status_code == 422
    for url in (
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/",
        "http://[::1]/",
        "http://10.0.0.5/",
        "ftp://example.com/job",
        "http://user:pass@example.com/",
    ):
        response = client.post("/api/v1/jobs/import-url", json={"url": url}, headers=headers)
        assert response.status_code == 422, url
        assert response.json()["error"]["code"] in {"url_blocked", "validation_error"}, url


def test_job_edit_reparses_and_analysis_requires_requirements(client):
    headers = auth_headers(client)
    resume = upload_resume(client, headers).json()
    job = create_job(client, headers).json()
    edited = client.patch(
        f"/api/v1/jobs/{job['id']}",
        json={
            "raw_text": "We are hiring a thoughtful person to join a friendly team and help us grow in many ways. " * 2
        },
        headers=headers,
    )
    assert edited.status_code == 200 and edited.json()["requirements_count"] == 0
    response = client.post("/api/v1/analysis", json={"resume_id": resume["id"], "job_id": job["id"]}, headers=headers)
    assert response.status_code == 422 and response.json()["error"]["code"] == "no_requirements"


def test_custom_weights_and_validation(client):
    headers = auth_headers(client)
    resume = upload_resume(client, headers).json()
    job = create_job(client, headers).json()
    body = {"resume_id": resume["id"], "job_id": job["id"], "scoring_weights": {"required_skills": 80, "structure": 0}}
    ok = client.post("/api/v1/analysis", json=body, headers=headers)
    assert ok.status_code == 201 and ok.json()["scoring_config"]["weights"]["required_skills"] == 80
    bad = client.post("/api/v1/analysis", json={**body, "scoring_weights": {"required_skills": 500}}, headers=headers)
    assert bad.status_code == 422


def test_delete_all_data_keeps_account(client):
    headers = auth_headers(client)
    upload_resume(client, headers)
    create_job(client, headers)
    assert client.delete("/api/v1/users/me/data", headers=headers).status_code == 204
    assert client.get("/api/v1/resumes", headers=headers).json()["total"] == 0
    assert client.get("/api/v1/jobs", headers=headers).json()["total"] == 0
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200


def test_health_and_error_shape(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/health/ready").json()["database"] == "ok"
    err = client.get("/api/v1/resumes/not-a-uuid", headers=auth_headers(client)).json()["error"]
    assert err["code"] == "validation_error" and "message" in err
