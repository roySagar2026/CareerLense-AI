import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GitCompare, History as HistoryIcon, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { ScoreBadge } from "@/components/ScoreBadge";
import { useAnalyses, useDeleteMutation } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { analysisApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { AnalysisSummary } from "@/types/api";
import { formatDateTime } from "@/utils/format";

export default function History() {
  const [company, setCompany] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [toDelete, setToDelete] = useState<AnalysisSummary | null>(null);
  const navigate = useNavigate();
  const toast = useToast();
  const { data, isLoading, isError, error, refetch } = useAnalyses({ company: company.trim(), job_title: jobTitle.trim(), page_size: 100 });
  const remove = useDeleteMutation(analysisApi.remove, () => {
    toast.success("Analysis deleted.");
    setSelected((s) => s.filter((id) => id !== toDelete?.id));
    setToDelete(null);
  });

  const toggle = (id: string) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length >= 2 ? [s[1], id] : [...s, id]));

  return (
    <div>
      <PageHeader
        title="Analysis history"
        description="Reopen, filter and compare earlier analyses."
        actions={<Button variant="secondary" disabled={selected.length !== 2} onClick={() => navigate(`/app/compare?a=${selected[0]}&b=${selected[1]}`)}><GitCompare className="h-4 w-4" />Compare selected ({selected.length}/2)</Button>}
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <Input className="max-w-xs" placeholder="Filter by company" aria-label="Filter by company" value={company} onChange={(e) => setCompany(e.target.value)} />
        <Input className="max-w-xs" placeholder="Filter by job title" aria-label="Filter by job title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
      </div>

      {isLoading ? <Skeleton className="h-64" /> : isError ? <ErrorState error={error} onRetry={() => refetch()} /> : data && data.items.length === 0 ? (
        <EmptyState icon={HistoryIcon} title={company || jobTitle ? "No analyses match these filters" : "No analyses yet"} description={company || jobTitle ? undefined : "Your completed analyses will appear here."} action={!company && !jobTitle ? <Button asChild><Link to="/app/analyze">New analysis</Link></Button> : undefined} />
      ) : (
        <Card>
          <ul className="divide-y">
            {data?.items.map((a) => (
              <li key={a.id} className="flex items-center gap-3 px-4 py-3">
                <input type="checkbox" className="h-4 w-4 accent-[#3978F6]" checked={selected.includes(a.id)} onChange={() => toggle(a.id)} aria-label={`Select ${a.job_title} analysis for comparison`} />
                <Link to={`/app/analysis/${a.id}`} className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{a.job_title}{a.company ? ` · ${a.company}` : ""}</p>
                  <p className="truncate text-xs text-muted">{a.resume_name} v{a.resume_version} · {formatDateTime(a.created_at)}</p>
                </Link>
                <ScoreBadge score={a.overall_score} />
                <Button variant="ghost" size="icon" aria-label={`Delete analysis of ${a.job_title}`} onClick={() => setToDelete(a)}><Trash2 className="h-4 w-4" /></Button>
              </li>
            ))}
          </ul>
        </Card>
      )}
      <ConfirmDialog open={toDelete !== null} onOpenChange={(o) => !o && setToDelete(null)} title="Delete this analysis?" description="The results will be permanently deleted. Your resume and job description are kept." confirmLabel="Delete analysis" loading={remove.isPending} onConfirm={() => toDelete && remove.mutate(toDelete.id, { onError: (e) => toast.error(errorMessage(e)) })} />
    </div>
  );
}
