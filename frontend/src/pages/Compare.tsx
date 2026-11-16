import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { chartColors, tooltipStyle } from "@/utils/chartTheme";
import { ArrowDown, ArrowRight, ArrowUp } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Field";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { ScoreBadge } from "@/components/ScoreBadge";
import { useAnalyses } from "@/hooks/useQueries";
import { analysisApi } from "@/services/api";
import type { DimensionKey } from "@/types/api";
import { cn } from "@/utils/cn";
import { GitCompare } from "lucide-react";

const DIMS: DimensionKey[] = ["required_skills", "preferred_skills", "experience", "responsibilities", "education", "structure"];

function Delta({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted">n/a</span>;
  const rounded = Math.round(value * 10) / 10;
  const Icon = rounded > 0 ? ArrowUp : rounded < 0 ? ArrowDown : ArrowRight;
  return (
    <span className={cn("inline-flex items-center gap-1 tabular-nums", rounded > 0 ? "text-success" : rounded < 0 ? "text-danger" : "text-muted")}>
      <Icon className="h-3.5 w-3.5" aria-hidden />{rounded > 0 ? "+" : ""}{rounded}
    </span>
  );
}

export default function Compare() {
  const [params, setParams] = useSearchParams();
  const a = params.get("a") ?? "";
  const b = params.get("b") ?? "";
  const list = useAnalyses({ page_size: 100 });
  const set = (key: "a" | "b", v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(key, v); else next.delete(key);
    setParams(next, { replace: true });
  };
  const cmp = useQuery({ queryKey: ["compare", a, b], queryFn: () => analysisApi.compare(a, b), enabled: Boolean(a && b && a !== b) });
  const jobId = cmp.data && cmp.data.a.job_id === cmp.data.b.job_id ? cmp.data.a.job_id : null;
  const trend = useQuery({ queryKey: ["trend", jobId], queryFn: () => analysisApi.trend(jobId as string), enabled: Boolean(jobId) });

  const options = list.data?.items ?? [];
  const label = (x: (typeof options)[number]) => `${x.job_title}${x.company ? ` · ${x.company}` : ""} — ${x.resume_name} v${x.resume_version} (${Math.round(x.overall_score)})`;

  return (
    <div>
      <PageHeader title="Compare analyses" description="See how score and keyword coverage changed, for example between resume versions." />
      {list.isLoading ? <Skeleton className="h-24" /> : list.isError ? <ErrorState error={list.error} onRetry={() => list.refetch()} /> : options.length < 2 ? (
        <EmptyState icon={GitCompare} title="You need at least two analyses" description="Run another analysis (for example with a new resume version) to compare results." action={<Link className="text-accent hover:underline" to="/app/analyze">New analysis</Link>} />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm">Baseline (A)<Select className="mt-1" value={a} onChange={(e) => set("a", e.target.value)}><option value="">Select…</option>{options.map((o) => <option key={o.id} value={o.id}>{label(o)}</option>)}</Select></label>
          <label className="text-sm">Compare to (B)<Select className="mt-1" value={b} onChange={(e) => set("b", e.target.value)}><option value="">Select…</option>{options.map((o) => <option key={o.id} value={o.id}>{label(o)}</option>)}</Select></label>
        </div>
      )}
      {a && b && a === b && <p role="alert" className="mt-4 text-sm text-warning">Pick two different analyses.</p>}

      {cmp.isLoading && <Skeleton className="mt-6 h-64" />}
      {cmp.isError && <div className="mt-6"><ErrorState error={cmp.error} onRetry={() => cmp.refetch()} /></div>}
      {cmp.data && (
        <div className="mt-6 space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            {[cmp.data.a, cmp.data.b].map((x, i) => (
              <Card key={x.id} className="p-4">
                <p className="text-xs text-muted">{i === 0 ? "A" : "B"}</p>
                <Link to={`/app/analysis/${x.id}`} className="font-medium hover:underline">{x.resume_name} v{x.resume_version}</Link>
                <p className="truncate text-xs text-muted">{x.job_title}</p>
                <div className="mt-2"><ScoreBadge score={x.overall_score} /></div>
              </Card>
            ))}
            <Card className="flex flex-col justify-center p-4">
              <p className="text-xs text-muted">Overall change</p>
              <p className="text-3xl font-semibold"><Delta value={cmp.data.score_delta} /></p>
            </Card>
          </div>

          <Card>
            <CardHeader title="Dimension changes" />
            <ul className="divide-y">
              {DIMS.map((k) => (
                <li key={k} className="flex items-center justify-between px-5 py-2.5 text-sm">
                  <span>{cmp.data.a.dimension_scores[k].label}</span>
                  <span className="flex items-center gap-4 text-muted tabular-nums">
                    {cmp.data.a.dimension_scores[k].score === null ? "n/a" : Math.round(cmp.data.a.dimension_scores[k].score as number)} → {cmp.data.b.dimension_scores[k].score === null ? "n/a" : Math.round(cmp.data.b.dimension_scores[k].score as number)}
                    <Delta value={cmp.data.dimension_deltas[k]} />
                  </span>
                </li>
              ))}
            </ul>
          </Card>

          <div className="grid gap-4 md:grid-cols-3">
            {([["Improved", cmp.data.improved_keywords, "success"], ["Regressed", cmp.data.regressed_keywords, "danger"], ["Still missing", cmp.data.unchanged_missing, "neutral"]] as const).map(([title, items, tone]) => (
              <Card key={title}>
                <CardHeader title={`${title} (${items.length})`} />
                <CardBody className="flex flex-wrap gap-1.5">{items.length === 0 ? <span className="text-sm text-muted">None</span> : items.map((k) => <Badge key={k} tone={tone}>{k}</Badge>)}</CardBody>
              </Card>
            ))}
          </div>

          {trend.data && trend.data.length > 1 && (
            <Card>
              <CardHeader title="Score by resume version" description="For this job description" />
              <CardBody>
                <div className="h-56" role="img" aria-label="Line chart of score by resume version">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trend.data.map((t) => ({ name: `${t.resume_name} v${t.resume_version}`, score: t.overall_score }))} margin={{ left: -20, right: 12 }}>
                      <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" stroke={chartColors.axis} tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 100]} stroke={chartColors.axis} tick={{ fontSize: 12 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Line type="monotone" dataKey="score" stroke={chartColors.primary} strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
