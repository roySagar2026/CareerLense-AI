import type { BadgeTone } from "@/components/ui/Badge";
import type { Importance, KeywordMatch, ResultCategory } from "@/types/api";

export const CATEGORY_META: Record<ResultCategory, { label: string; tone: BadgeTone; help: string }> = {
  exact: { label: "Exact match", tone: "success", help: "Found with demonstrated or listed evidence." },
  semantic: { label: "Related skill", tone: "warning", help: "A related skill was found. Possession of this exact skill is NOT verified." },
  partial: { label: "Partial match", tone: "accent", help: "A spelling variant or only a weak mention was found." },
  missing_mandatory: { label: "Missing (required)", tone: "danger", help: "Required by the job but not found in the resume." },
  missing_preferred: { label: "Missing (preferred)", tone: "warning", help: "Preferred by the job but not found in the resume." },
  contextual: { label: "Contextual", tone: "neutral", help: "A lower-importance keyword such as a soft skill or background mention." },
};

export const IMPORTANCE_TONE: Record<Importance, BadgeTone> = { required: "danger", preferred: "primary", contextual: "neutral" };

export const MATCH_TYPE_LABEL: Record<KeywordMatch["match_type"], string> = {
  exact: "Exact",
  fuzzy: "Fuzzy",
  semantic: "Related",
  implied: "Implied",
  partial: "Partial",
  missing: "Not found",
};

export const PRIORITY_TONE = { high: "danger", medium: "warning", low: "neutral" } as const;
