import { MapPin } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { useKeywords } from "@/hooks/useQueries";
import type { KeywordMatch } from "@/types/api";
import { titleCase } from "@/utils/format";
import { IMPORTANCE_TONE } from "./labels";

/** Missing keywords with the resume section where they would most naturally fit, if the candidate genuinely has the experience. */
export function PlacementSuggestions({ analysisId }: { analysisId: string }) {
  const required = useKeywords(analysisId, { result_category: "missing_mandatory", page_size: 100 });
  const preferred = useKeywords(analysisId, { result_category: "missing_preferred", page_size: 100 });
  if (required.isLoading || preferred.isLoading) return <Skeleton className="h-48" />;
  if (required.isError || preferred.isError) return <ErrorState error={required.error ?? preferred.error} onRetry={() => { void required.refetch(); void preferred.refetch(); }} />;
  const items: KeywordMatch[] = [...(required.data?.items ?? []), ...(preferred.data?.items ?? [])].filter((k) => k.kind === "skill");
  if (items.length === 0) return <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted">No missing skills. Nothing to place.</p>;
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">Where each missing skill would fit naturally <strong className="text-foreground">if you genuinely have that experience</strong>. If you don't, leave it out; honest gaps are better than invented skills.</p>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((k) => (
          <Card key={k.id} className="p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium">{k.normalized_keyword}</p>
              <Badge tone={IMPORTANCE_TONE[k.importance]}>{k.importance}</Badge>
            </div>
            <p className="mt-2 flex items-center gap-1.5 text-sm"><MapPin className="h-3.5 w-3.5 text-accent" aria-hidden />{k.suggested_section ? titleCase(k.suggested_section) : "Skills"}</p>
            <p className="mt-1 text-xs text-muted">{k.explanation}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
