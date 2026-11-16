// Mirrors docs/api-documentation.md — keep in sync with backend/app/schemas.

export interface ApiErrorBody {
  error: { code: string; message: string; details?: unknown };
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface PrivacySettings {
  retention_days: number | null;
  store_original_files: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  headline: string | null;
  created_at: string;
  privacy_settings: PrivacySettings;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export type SectionType =
  | "summary"
  | "skills"
  | "experience"
  | "projects"
  | "education"
  | "certifications"
  | "achievements"
  | "contact"
  | "other";

export type EvidenceLevel = "demonstrated" | "listed" | "mentioned";

export interface Resume {
  id: string;
  name: string;
  version: number;
  parent_resume_id: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: "ready" | "failed";
  extraction_method: "pymupdf" | "pypdf" | "ocr" | "docx" | null;
  extraction_confidence: number | null;
  page_count: number | null;
  word_count: number;
  error_message: string | null;
  has_original_file: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeSection {
  id: string;
  section_type: SectionType;
  heading_text: string | null;
  content: string;
  order_index: number;
  page_start: number | null;
  confidence: number;
  user_edited: boolean;
}

export interface ExtractedSkill {
  id: string;
  canonical_name: string;
  surface_form: string;
  category: string;
  section_type: string | null;
  context_snippet: string | null;
  evidence_level: EvidenceLevel;
  occurrences: number;
}

export interface ParsedData {
  contact: { name: string | null; email: string | null; phone: string | null; links: string[] };
  experience: {
    title: string | null;
    organization: string | null;
    date_range: string | null;
    bullets: string[];
  }[];
  education: { degree: string | null; institution: string | null; year: string | null }[];
  certifications: string[];
  projects: { name: string; tech: string[]; bullets: string[] }[];
  estimated_years_experience: number;
  highest_degree_level: number;
}

export interface ResumeDetail extends Resume {
  sections: ResumeSection[];
  skills: ExtractedSkill[];
  parsed_data: ParsedData;
  raw_text: string;
  warnings: string[];
}

export type RequirementKind =
  | "skill"
  | "responsibility"
  | "experience"
  | "education"
  | "certification";
export type Importance = "required" | "preferred" | "contextual";

export interface Job {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  source_type: "paste" | "url";
  source_url: string | null;
  requirements_count: number;
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: string;
  kind: RequirementKind;
  canonical_name: string;
  surface_form: string;
  importance: Importance;
  category: string;
  evidence_snippet: string | null;
  min_years: number | null;
}

export interface JobDetail extends Job {
  raw_text: string;
  requirements: Requirement[];
}

export type DimensionKey =
  | "required_skills"
  | "preferred_skills"
  | "experience"
  | "responsibilities"
  | "education"
  | "structure";

export interface Dimension {
  score: number | null;
  weight: number;
  effective_weight: number | null;
  contribution: number;
  label: string;
  explanation: string;
}

export interface AnalysisSummary {
  id: string;
  resume_id: string;
  resume_name: string;
  resume_version: number;
  job_id: string;
  job_title: string;
  company: string | null;
  overall_score: number;
  status: "completed";
  engine_version: string;
  dimension_scores: Record<DimensionKey, Dimension>;
  created_at: string;
}

export type Priority = "high" | "medium" | "low";

export interface SkillComparisonRow {
  keyword: string;
  importance: Importance;
  status: "matched" | "partial" | "missing";
  evidence_level: EvidenceLevel | null;
  match_type: string;
  note: string;
}

export interface SectionAnalysis {
  section_type: string;
  present: boolean;
  priority: Priority;
  strengths: string[];
  missing: string[];
  relevant_keywords: string[];
  recommendations: string[];
}

export interface AnalysisDetail extends AnalysisSummary {
  disclaimer: string;
  scoring_config: { weights: Record<DimensionKey, number>; formula: string };
  metrics: {
    skills_alignment: number | null;
    keyword_coverage: number | null;
    structural_quality: number;
    experience_alignment: number | null;
    education_alignment: number | null;
  };
  keyword_counts: {
    exact: number;
    semantic: number;
    partial: number;
    missing_mandatory: number;
    missing_preferred: number;
    contextual: number;
  };
  skills_comparison: SkillComparisonRow[];
  section_analysis: SectionAnalysis[];
}

export type ResultCategory =
  | "exact"
  | "semantic"
  | "partial"
  | "missing_mandatory"
  | "missing_preferred"
  | "contextual";

export interface KeywordMatch {
  id: string;
  requirement_id: string;
  original_keyword: string;
  normalized_keyword: string;
  kind: RequirementKind;
  importance: Importance;
  category: string;
  match_type: "exact" | "fuzzy" | "semantic" | "implied" | "partial" | "missing";
  result_category: ResultCategory;
  similarity: number;
  confidence: number;
  credit: number;
  occurrences: number;
  evidence_level: string | null;
  source_section: string | null;
  suggested_section: string | null;
  explanation: string;
}

export interface Recommendation {
  id: string;
  section_type: string;
  priority: Priority;
  kind: "add_keyword" | "strengthen_evidence" | "quantify" | "structure" | "clarify" | "verify";
  title: string;
  detail: string;
  related_keyword: string | null;
  is_suggestion: true;
  caveat: string | null;
  example_template: string | null;
}

export interface Comparison {
  a: AnalysisSummary;
  b: AnalysisSummary;
  score_delta: number;
  dimension_deltas: Record<DimensionKey, number | null>;
  improved_keywords: string[];
  regressed_keywords: string[];
  unchanged_missing: string[];
}

export interface TrendPoint {
  analysis_id: string;
  resume_id: string;
  resume_name: string;
  resume_version: number;
  overall_score: number;
  created_at: string;
}

export interface DashboardSummary {
  total_resumes: number;
  total_jobs: number;
  total_analyses: number;
  average_score: number | null;
  best_resume: {
    id: string;
    name: string;
    version: number;
    average_score: number;
    analyses_count: number;
  } | null;
  recent_analyses: AnalysisSummary[];
  score_history: { date: string; score: number }[];
}

export interface ActivityItem {
  id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  label: string;
  created_at: string;
}
