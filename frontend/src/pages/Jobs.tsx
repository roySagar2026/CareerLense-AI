import { useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Search, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { JobForms } from "@/components/JobForms";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { useDeleteMutation, useJobs } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { jobsApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { Job } from "@/types/api";
import { formatDate } from "@/utils/format";
import { useNavigate } from "react-router-dom";


export default function Jobs() {
  const [search, setSearch] = useState("");
  const [toDelete, setToDelete] = useState<Job | null>(null);
  const toast = useToast();
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useJobs(search.trim() || undefined);
  const remove = useDeleteMutation(jobsApi.remove, () => {
    toast.success("Job description deleted.");
    setToDelete(null);
  });

  return (
    <div>
      <PageHeader title="Job descriptions" description="Save the roles you're targeting." />
      <Card>
        <CardHeader title="Add a job description" />
        <CardBody><JobForms onCreated={(j) => navigate(`/app/jobs/${j.id}`)} /></CardBody>
      </Card>

      <div className="relative mb-4 mt-8 max-w-xs">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
        <Input className="pl-9" placeholder="Search by title or company" aria-label="Search jobs" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {isLoading ? (
        <div className="space-y-3">{[0, 1].map((i) => <Skeleton key={i} className="h-20" />)}</div>
      ) : isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : data && data.items.length === 0 ? (
        <EmptyState icon={Briefcase} title={search ? "No matching jobs" : "No job descriptions yet"} description={search ? "Try a different search." : "Paste a job description above to get started."} />
      ) : (
        <ul className="space-y-3">
          {data?.items.map((j) => (
            <li key={j.id}>
              <Card className="flex items-center justify-between gap-4 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift">
                <Link to={`/app/jobs/${j.id}`} className="min-w-0 flex-1">
                  <p className="truncate font-medium">{j.title}{j.company ? ` · ${j.company}` : ""}</p>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                    {j.location && <span>{j.location}</span>}
                    <Badge>{j.requirements_count} requirements</Badge>
                    {j.source_type === "url" && <Badge tone="accent">Imported</Badge>}
                    <span>{formatDate(j.created_at)}</span>
                  </p>
                </Link>
                <Button variant="ghost" size="icon" aria-label={`Delete ${j.title}`} onClick={() => setToDelete(j)}><Trash2 className="h-4 w-4" /></Button>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog open={toDelete !== null} onOpenChange={(o) => !o && setToDelete(null)} title="Delete this job description?" description={`“${toDelete?.title ?? ""}” and its analyses will be permanently deleted.`} confirmLabel="Delete" loading={remove.isPending} onConfirm={() => toDelete && remove.mutate(toDelete.id, { onError: (e) => toast.error(errorMessage(e)) })} />
    </div>
  );
}
