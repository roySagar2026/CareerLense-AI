# CareerLens AI — API contract (v1)

This file is the single source of truth shared by the backend (`backend/app/schemas`) and the frontend (`frontend/src/types`). Interactive OpenAPI docs are served by the backend at `/api/docs`.

**Conventions**

- Base path: `/api/v1`. Health: `GET /api/health`, `GET /api/health/ready` (not versioned).
- JSON, `snake_case`. IDs are UUID strings. Timestamps are ISO-8601 UTC strings.
- Auth: `Authorization: Bearer <access_token>` on everything except auth endpoints and health.
- Errors (every non-2xx): `{"error": {"code": string, "message": string, "details": any | null}}`
  - Codes: `validation_error` (422), `unauthorized` (401), `forbidden` (403), `not_found` (404), `conflict` (409), `rate_limited` (429), `file_too_large` (413), `unsupported_file_type` (415), `url_blocked` (422), `fetch_failed` (422), `no_content` (422), `no_requirements` (422), `internal_error` (500).
- Paged lists: `{"items": T[], "total": int, "page": int, "page_size": int}`; query `?page=1&page_size=20` (`page_size` max 100).
- Upload limit: **4 MB** (Vercel request-body limit is 4.5 MB). Types: PDF, DOCX.
- The overall score is a **heuristic alignment score**. It is never an employer ATS score. Every analysis payload carries a `disclaimer` string; the UI must show it.

## Auth

The refresh token is an httpOnly cookie (`cl_refresh`, path `/api/v1/auth`). The browser client must send `withCredentials: true` and, on `/auth/refresh` and `/auth/logout`, the header `X-Requested-With: CareerLens`. The access token lives in memory only.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{email, password, full_name?}` | 201 `AuthResponse` |
| POST | `/auth/login` | `{email, password}` | 200 `AuthResponse` |
| POST | `/auth/refresh` | none (cookie) | 200 `AuthResponse` |
| POST | `/auth/logout` | none (cookie) | 204 |
| POST | `/auth/forgot-password` | `{email}` | 202 `{message}` (always, never reveals whether the email exists) |
| POST | `/auth/reset-password` | `{token, new_password}` | 200 `{message}` |

Password rules: 10–128 chars, at least one letter and one digit.

```ts
AuthResponse = { user: User, access_token: string, token_type: "bearer", expires_in: number /* seconds */ }
User = { id, email, full_name: string|null, headline: string|null, created_at,
         privacy_settings: { retention_days: number|null, store_original_files: boolean } }
```

## Users

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/users/me` | | `User` |
| PATCH | `/users/me` | `{full_name?, headline?, privacy_settings?: {retention_days?: number\|null, store_original_files?: boolean}}` | `User` |
| POST | `/users/me/password` | `{current_password, new_password}` | 204 |
| DELETE | `/users/me/data` | | 204 — deletes all resumes, jobs and analyses; keeps the account |
| DELETE | `/users/me` | `{password}` (JSON body) | 204 — deletes the account and everything it owns |

## Resumes

```ts
Resume = { id, name, version: number, parent_resume_id: string|null, original_filename, mime_type,
  size_bytes, status: "ready"|"failed", extraction_method: "pymupdf"|"pypdf"|"ocr"|"docx"|null,
  extraction_confidence: number|null /* 0..1 */, page_count: number|null, word_count: number,
  error_message: string|null, has_original_file: boolean, created_at, updated_at }

ResumeSection = { id, section_type: "summary"|"skills"|"experience"|"projects"|"education"|
  "certifications"|"achievements"|"contact"|"other", heading_text: string|null, content: string,
  order_index: number, page_start: number|null, confidence: number, user_edited: boolean }

ExtractedSkill = { id, canonical_name, surface_form, category, section_type: string|null,
  context_snippet: string|null, evidence_level: "demonstrated"|"listed"|"mentioned", occurrences: number }

ParsedData = {
  contact: { name: string|null, email: string|null, phone: string|null, links: string[] },
  experience: { title: string|null, organization: string|null, date_range: string|null, bullets: string[] }[],
  education: { degree: string|null, institution: string|null, year: string|null }[],
  certifications: string[],
  projects: { name: string, tech: string[], bullets: string[] }[],
  estimated_years_experience: number,
  highest_degree_level: number /* 0 none,1 diploma,2 bachelor,3 master,4 doctorate */ }

ResumeDetail = Resume & { sections: ResumeSection[], skills: ExtractedSkill[], parsed_data: ParsedData,
  raw_text: string, warnings: string[] }
```

| Method | Path | Notes | Response |
|---|---|---|---|
| POST | `/resumes/upload` | multipart: `file`, `name?`, `parent_resume_id?` (creates version n+1). Parsing is synchronous. Invalid type/size → 4xx. A parse failure still returns 201 with `status:"failed"` and `error_message`. | 201 `ResumeDetail` |
| GET | `/resumes` | `?search=` | `Page<Resume>` |
| GET | `/resumes/{id}` | | `ResumeDetail` |
| PATCH | `/resumes/{id}` | `{name}` | `Resume` |
| PATCH | `/resumes/{id}/sections/{section_id}` | `{section_type?, heading_text?, content?}` — recomputes skills and parsed data | `ResumeDetail` |
| POST | `/resumes/{id}/reprocess` | re-parses the stored original; discards manual section edits | `ResumeDetail` |
| GET | `/resumes/{id}/file` | authorized stream of the original file (fetch as blob with the bearer token) | file |
| GET | `/resumes/{id}/versions` | the whole version chain, ordered by version | `Resume[]` |
| DELETE | `/resumes/{id}` | cascades to analyses of this resume | 204 |

## Jobs

```ts
Job = { id, title, company: string|null, location: string|null, source_type: "paste"|"url",
  source_url: string|null, requirements_count: number, created_at, updated_at }
Requirement = { id, kind: "skill"|"responsibility"|"experience"|"education"|"certification",
  canonical_name, surface_form, importance: "required"|"preferred"|"contextual",
  category: string, evidence_snippet: string|null, min_years: number|null }
JobDetail = Job & { raw_text: string, requirements: Requirement[] }
```

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/jobs` | `{title?, company?, location?, raw_text}` (`raw_text` 80–50000 chars) | 201 `JobDetail` |
| POST | `/jobs/import-url` | `{url, title?, company?, location?}` — SSRF-guarded. On failure the message tells the user to paste the text instead. | 201 `JobDetail` |
| GET | `/jobs` | `?search=` (title or company) | `Page<Job>` |
| GET | `/jobs/{id}` | | `JobDetail` |
| PATCH | `/jobs/{id}` | `{title?, company?, location?, raw_text?}` — re-parses when `raw_text` changes | `JobDetail` |
| DELETE | `/jobs/{id}` | | 204 |

## Analysis

```ts
DimensionKey = "required_skills"|"preferred_skills"|"experience"|"responsibilities"|"education"|"structure"
Dimension = { score: number|null /* 0..100; null = not applicable to this job */, weight: number,
  effective_weight: number|null /* % after redistributing weight of n/a dimensions */,
  contribution: number /* points added to the overall score */, label: string, explanation: string }

AnalysisSummary = { id, resume_id, resume_name, resume_version, job_id, job_title, company: string|null,
  overall_score: number /* 0..100 */, status: "completed", engine_version: string,
  dimension_scores: Record<DimensionKey, Dimension>, created_at }

AnalysisDetail = AnalysisSummary & {
  disclaimer: string,
  scoring_config: { weights: Record<DimensionKey, number>, formula: string },
  metrics: { skills_alignment: number|null, keyword_coverage: number|null, structural_quality: number,
             experience_alignment: number|null, education_alignment: number|null },
  keyword_counts: { exact, semantic, partial, missing_mandatory, missing_preferred, contextual: number },
  skills_comparison: { keyword: string, importance: Importance, status: "matched"|"partial"|"missing",
    evidence_level: "demonstrated"|"listed"|"mentioned"|null, match_type: string, note: string }[],
  section_analysis: { section_type: string, present: boolean, priority: "high"|"medium"|"low",
    strengths: string[], missing: string[], relevant_keywords: string[], recommendations: string[] }[] }

KeywordMatch = { id, requirement_id, original_keyword, normalized_keyword, kind: RequirementKind,
  importance: Importance, category: string, match_type: "exact"|"fuzzy"|"semantic"|"implied"|"partial"|"missing",
  result_category: "exact"|"semantic"|"partial"|"missing_mandatory"|"missing_preferred"|"contextual",
  similarity: number /* 0..1 */, confidence: number /* 0..1 */, credit: number /* 0..1 */,
  occurrences: number, evidence_level: string|null, source_section: string|null,
  suggested_section: string|null, explanation: string }

Recommendation = { id, section_type: string, priority: "high"|"medium"|"low",
  kind: "add_keyword"|"strengthen_evidence"|"quantify"|"structure"|"clarify"|"verify",
  title, detail, related_keyword: string|null, is_suggestion: true /* always: suggestions are never facts */,
  caveat: string|null, example_template: string|null /* placeholders in [brackets], never invented facts */ }
```

| Method | Path | Notes | Response |
|---|---|---|---|
| POST | `/analysis` | `{resume_id, job_id, scoring_weights?: Partial<Record<DimensionKey, number>>}` weights 0–100, at least one > 0. Synchronous. `422 no_requirements` when the job has nothing extractable. | 201 `AnalysisDetail` |
| GET | `/analysis` | `?company=&job_title=&resume_id=&job_id=` (case-insensitive contains) | `Page<AnalysisSummary>` |
| GET | `/analysis/compare` | `?a=<id>&b=<id>` | `{a: AnalysisSummary, b: AnalysisSummary, score_delta: number, dimension_deltas: Record<DimensionKey, number|null>, improved_keywords: string[], regressed_keywords: string[], unchanged_missing: string[]}` |
| GET | `/analysis/trend` | `?job_id=` — score by resume version for one job | `{analysis_id, resume_id, resume_name, resume_version, overall_score, created_at}[]` |
| GET | `/analysis/{id}` | | `AnalysisDetail` |
| DELETE | `/analysis/{id}` | | 204 |
| GET | `/analysis/{id}/keywords` | `?result_category=&kind=&importance=&search=&page=&page_size=` | `Page<KeywordMatch>` |
| GET | `/analysis/{id}/recommendations` | `?priority=&section_type=` | `Recommendation[]` |

`result_category` meaning: `exact` = found with demonstrated or listed evidence; `semantic` = a related (same-family) skill found, **not verified** possession; `partial` = typo/variant (fuzzy) match or only a weak mention; `missing_mandatory` / `missing_preferred` = not found; `contextual` = a low-importance job keyword (soft skill or background mention).

## Dashboard

| Method | Path | Response |
|---|---|---|
| GET | `/dashboard/summary` | `{total_resumes, total_jobs, total_analyses, average_score: number\|null, best_resume: {id, name, version, average_score, analyses_count}\|null, recent_analyses: AnalysisSummary[], score_history: {date, score}[]}` |
| GET | `/dashboard/recent-activity?limit=10` | `{id, action, resource_type: string\|null, resource_id: string\|null, label: string, created_at}[]` |
