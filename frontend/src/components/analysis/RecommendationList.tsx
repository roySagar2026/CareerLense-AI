import { useState } from "react";
import { Lightbulb, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { useRecommendations } from "@/hooks/useQueries";
import type { Recommendation } from "@/types/api";
import { titleCase } from "@/utils/format";
import { PRIORITY_TONE } from "./labels";

function Item({ r }: { r: Recommendation }) {
  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={PRIORITY_TONE[r.priority]}>{r.priority}</Badge>
        <Badge>{titleCase(r.section_type)}</Badge>
        <Badge tone="accent">Suggestion</Badge>
      </div>
      <h3 className="mt-2 font-medium">{r.title}</h3>
      <p className="mt-1 text-sm text-muted">{r.detail}</p>
      {r.caveat && (
        <p className="mt-3 flex gap-2 rounded-md border border-warning/30 bg-warning/5 p-2.5 text-xs">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden />
          {r.caveat}
        </p>
      )}
      {r.example_template && (
        <div className="mt-3">
          <p className="mb-1 text-xs text-muted">Template only. Replace the [bracketed] parts with your real details:</p>
          <p className="rounded-md border bg-surface p-2.5 font-mono text-xs">{r.example_template}</p>
        </div>
      )}
    </Card>
  );
}

export function RecommendationList({ analysisId }: { analysisId: string }) {
  const [priority, setPriority] = useState("");
  const { data, isLoading, isError, error, refetch } = useRecommendations(analysisId, priority || undefined);
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-lg border bg-surface p-3 text-sm">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden />
        <p className="text-muted">These are <strong className="text-foreground">suggestions</strong>, not facts about you. Only add a skill or achievement if it is true. Nothing here has been added to your resume.</p>
      </div>
      <div className="flex gap-2" role="group" aria-label="Filter by priority">
        {["", "high", "medium", "low"].map((p) => (
          <Button key={p || "all"} size="sm" variant={priority === p ? "primary" : "secondary"} aria-pressed={priority === p} onClick={() => setPriority(p)}>{p ? titleCase(p) : "All"}</Button>
        ))}
      </div>
      {isLoading ? <Skeleton className="h-48" /> : isError ? <ErrorState error={error} onRetry={() => refetch()} /> : data && data.length === 0 ? (
        <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted">No recommendations for this filter.</p>
      ) : (
        <div className="space-y-3">{data?.map((r) => <Item key={r.id} r={r} />)}</div>
      )}
    </div>
  );
}
