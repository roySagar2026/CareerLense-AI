import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { AnalysisDetail } from "@/types/api";
import { IMPORTANCE_TONE } from "./labels";

const STATUS = {
  matched: { icon: CheckCircle2, cls: "text-success", label: "Matched" },
  partial: { icon: CircleDashed, cls: "text-warning", label: "Partially demonstrated" },
  missing: { icon: XCircle, cls: "text-danger", label: "Missing" },
} as const;

export function SkillsComparison({ analysis }: { analysis: AnalysisDetail }) {
  const rows = analysis.skills_comparison;
  if (rows.length === 0) return <p className="text-sm text-muted">This job description doesn't list specific skills to compare.</p>;
  const tally = { matched: 0, partial: 0, missing: 0 };
  rows.forEach((r) => (tally[r.status] += 1));
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        {tally.matched} matched · {tally.partial} partial · {tally.missing} missing. A skill counts as demonstrated only when your resume shows it being used, not merely when the word appears.
      </p>
      <Card>
        <ul className="divide-y">
          {rows.map((r) => {
            const s = STATUS[r.status];
            const Icon = s.icon;
            return (
              <li key={r.keyword} className="flex flex-wrap items-start gap-x-4 gap-y-1 px-4 py-3">
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${s.cls}`} aria-label={s.label} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{r.keyword}</span>
                    <Badge tone={IMPORTANCE_TONE[r.importance]}>{r.importance}</Badge>
                    {r.evidence_level && <Badge>{r.evidence_level}</Badge>}
                    <span className="text-xs text-muted">{s.label}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted">{r.note}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </Card>
    </div>
  );
}
