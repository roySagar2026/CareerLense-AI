import { useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Search, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { ResumeUploader } from "@/components/ResumeUploader";
import { useDeleteMutation, useResumes } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { resumesApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { Resume } from "@/types/api";
import { formatBytes, formatDate } from "@/utils/format";

export default function Resumes() {
  const [search, setSearch] = useState("");
  const [toDelete, setToDelete] = useState<Resume | null>(null);
  const toast = useToast();
  const { data, isLoading, isError, error, refetch } = useResumes(search.trim() || undefined);
  const remove = useDeleteMutation(resumesApi.remove, () => {
    toast.success("Resume deleted.");
    setToDelete(null);
  });

  return (
    <div>
      <PageHeader title="Resumes" description="Upload, review and manage your resume versions." />
      <ResumeUploader />

      <div className="mb-4 mt-8 flex items-center gap-3">
        <div className="relative max-w-xs flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
          <Input className="pl-9" placeholder="Search resumes" aria-label="Search resumes" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-20" />)}</div>
      ) : isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : data && data.items.length === 0 ? (
        <EmptyState icon={FileText} title={search ? "No matching resumes" : "No resumes yet"} description={search ? "Try a different search." : "Upload a PDF or DOCX above to get started."} />
      ) : (
        <ul className="space-y-3">
          {data?.items.map((r) => (
            <li key={r.id}>
              <Card className="flex items-center justify-between gap-4 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift">
                <Link to={`/app/resumes/${r.id}`} className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="truncate font-medium">{r.name}</span>
                    <Badge tone="primary">v{r.version}</Badge>
                    {r.status === "failed" ? <Badge tone="danger">Extraction failed</Badge> : <Badge tone="success">Ready</Badge>}
                  </div>
                  <p className="mt-1 truncate text-xs text-muted">
                    {r.original_filename} · {formatBytes(r.size_bytes)} · {r.word_count} words · {formatDate(r.created_at)}
                  </p>
                </Link>
                <Button variant="ghost" size="icon" aria-label={`Delete ${r.name}`} onClick={() => setToDelete(r)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={toDelete !== null}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete this resume?"
        description={`“${toDelete?.name ?? ""}” and every analysis that used it will be permanently deleted.`}
        confirmLabel="Delete resume"
        loading={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id, { onError: (e) => toast.error(errorMessage(e)) })}
      />
    </div>
  );
}
