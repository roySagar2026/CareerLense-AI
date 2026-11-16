import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreOverview } from "./ScoreOverview";
import { SkillsComparison } from "./SkillsComparison";
import { SectionAnalysisView } from "./SectionAnalysisView";
import type { AnalysisDetail, Dimension, DimensionKey } from "@/types/api";

const dim = (label: string, score: number | null, weight: number): Dimension => ({
  score, weight, effective_weight: score === null ? null : weight, contribution: score === null ? 0 : (score * weight) / 100, label, explanation: `${label} explanation`,
});

const analysis: AnalysisDetail = {
  id: "a1", resume_id: "r1", resume_name: "My Resume", resume_version: 1, job_id: "j1", job_title: "Backend Engineer", company: "Northwind",
  overall_score: 48.4, status: "completed", engine_version: "1.0", created_at: "2026-01-01T00:00:00Z",
  disclaimer: "This is a heuristic alignment score. It is NOT the score of any employer's ATS.",
  dimension_scores: {
    required_skills: dim("Required skills", 60, 35), preferred_skills: dim("Preferred skills", 20, 15), experience: dim("Experience", 80, 20),
    responsibilities: dim("Responsibilities", 40, 15), education: dim("Education", null, 10), structure: dim("Structure", 90, 5),
  } as Record<DimensionKey, Dimension>,
  scoring_config: { weights: { required_skills: 35, preferred_skills: 15, experience: 20, responsibilities: 15, education: 10, structure: 5 }, formula: "Weighted average of applicable dimensions." },
  metrics: { skills_alignment: 55, keyword_coverage: 50, structural_quality: 90, experience_alignment: 80, education_alignment: null },
  keyword_counts: { exact: 4, semantic: 1, partial: 0, missing_mandatory: 2, missing_preferred: 1, contextual: 0 },
  skills_comparison: [
    { keyword: "Python", importance: "required", status: "matched", evidence_level: "demonstrated", match_type: "exact", note: "Used in a project." },
    { keyword: "Docker", importance: "required", status: "missing", evidence_level: null, match_type: "missing", note: "Not found." },
  ],
  section_analysis: [
    { section_type: "projects", present: true, priority: "high", strengths: ["Describes a backend project"], missing: ["No metrics"], relevant_keywords: ["Python"], recommendations: ["Add measurable outcomes"] },
  ],
};

describe("analysis views", () => {
  it("always shows the not-an-ATS-score disclaimer and rounds the score", () => {
    render(<ScoreOverview analysis={analysis} />);
    expect(screen.getByRole("note")).toHaveTextContent("NOT the score of any employer's ATS");
    expect(screen.getByRole("img", { name: /Overall alignment score: 48 out of 100/ })).toBeInTheDocument();
    expect(screen.getAllByText("n/a").length).toBeGreaterThan(0); // education not applicable
  });

  it("separates matched and missing skills", () => {
    render(<SkillsComparison analysis={analysis} />);
    expect(screen.getByText(/1 matched · 0 partial · 1 missing/)).toBeInTheDocument();
    expect(screen.getByLabelText("Matched")).toBeInTheDocument();
    expect(screen.getByLabelText("Missing")).toBeInTheDocument();
  });

  it("renders section analysis with priority", () => {
    render(<SectionAnalysisView analysis={analysis} />);
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("high priority")).toBeInTheDocument();
    expect(screen.getByText("Add measurable outcomes")).toBeInTheDocument();
  });
});
