import { Link } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { chartColors, tooltipStyle } from "@/utils/chartTheme";
import { Briefcase, FileText, Gauge, History as HistoryIcon, Sparkles, Trophy } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { PageSkeleton, Skeleton } from "@/components/ui/Skeleton";
import { ScoreBadge } from "@/components/ScoreBadge";
import { useActivity, useDashboard } from "@/hooks/useQueries";
import { useAuth } from "@/contexts/AuthContext";
import { formatDateTime, formatScore } from "@/utils/format";

function Stat({ icon: Icon, label, value, hint }: { icon: typeof FileText; label: string; value: string; hint?: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Icon className="h-4 w-4 text-accent" aria-hidden />
        {label}
      </div>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-0.5 truncate text-xs text-muted">{hint}</p>}
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const summary = useDashboard();
  const activity = useActivity();

  if (summary.isLoading) return <PageSkeleton />;
  if (summary.isError) return <ErrorState error={summary.error} onRetry={() => summary.refetch()} />;
  const d = summary.data;
  if (!d) return null;

  const chartData = d.score_history.map((p) => ({ date: new Date(p.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }), score: p.score }));

  return (
    <div>
      <PageHeader
        title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
        description="Your resumes, job descriptions and analyses at a glance."
        actions={
          <>
            <Button asChild variant="secondary"><Link to="/app/resumes">Upload resume</Link></Button>
            <Button asChild><Link to="/app/analyze"><Sparkles className="h-4 w-4" />New analysis</Link></Button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={FileText} label="Resumes" value={String(d.total_resumes)} />
        <Stat icon={Briefcase} label="Jobs analyzed" value={String(d.total_jobs)} />
        <Stat icon={Gauge} label="Average score" value={formatScore(d.average_score)} hint="Heuristic alignment" />
        <Stat
          icon={Trophy}
          label="Best resume"
          value={d.best_resume ? formatScore(d.best_resume.average_score) : "—"}
          hint={d.best_resume ? `${d.best_resume.name} v${d.best_resume.version}` : "Run an analysis first"}
        />
      </div>

      {d.total_analyses === 0 ? (
        <div className="mt-6">
          <EmptyState
            icon={Sparkles}
            title="Run your first analysis"
            description="Upload a resume and add a job description to see matched and missing keywords."
            action={
              d.total_resumes === 0 ? (
                <Button asChild><Link to="/app/resumes">Upload a resume</Link></Button>
              ) : (
                <Button asChild><Link to="/app/analyze">Start analysis</Link></Button>
              )
            }
          />
        </div>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-5">
          <Card className="lg:col-span-3">
            <CardHeader title="Score over time" description="Overall score of each analysis you've run" />
            <CardBody>
              <div className="h-56" aria-label="Score history chart" role="img">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ left: -20, right: 8, top: 8 }}>
                    <defs>
                      <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={chartColors.primary} stopOpacity={0.4} />
                        <stop offset="100%" stopColor={chartColors.primary} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" stroke={chartColors.axis} tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} stroke={chartColors.axis} tick={{ fontSize: 12 }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area type="monotone" dataKey="score" stroke={chartColors.primary} strokeWidth={2} fill="url(#scoreFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardBody>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader title="Recent activity" />
            <CardBody>
              {activity.isLoading ? (
                <Skeleton className="h-32" />
              ) : activity.data && activity.data.length > 0 ? (
                <ul className="space-y-3">
                  {activity.data.map((a) => (
                    <li key={a.id} className="text-sm">
                      <p>{a.label}</p>
                      <p className="text-xs text-muted">{formatDateTime(a.created_at)}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted">No activity yet.</p>
              )}
            </CardBody>
          </Card>

          <Card className="lg:col-span-5">
            <CardHeader
              title="Recent analyses"
              action={
                <Button asChild variant="ghost" size="sm"><Link to="/app/history"><HistoryIcon className="h-4 w-4" />All history</Link></Button>
              }
            />
            <ul className="divide-y">
              {d.recent_analyses.map((a) => (
                <li key={a.id}>
                  <Link to={`/app/analysis/${a.id}`} className="flex items-center justify-between gap-4 px-5 py-3 hover:bg-surface/60">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{a.job_title}{a.company ? ` · ${a.company}` : ""}</p>
                      <p className="truncate text-xs text-muted">{a.resume_name} v{a.resume_version} · {formatDateTime(a.created_at)}</p>
                    </div>
                    <ScoreBadge score={a.overall_score} />
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
