import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ExternalLink, Pencil, Sparkles, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Field";
import { ErrorState } from "@/components/ui/States";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useDeleteMutation, useInvalidateAll, useJob } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { jobsApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { Importance, Requirement } from "@/types/api";
import { titleCase } from "@/utils/format";

const tone: Record<Importance, BadgeTone> = { required: "danger", preferred: "primary", contextual: "neutral" };

function Group({ title, items }: { title: string; items: Requirement[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-medium">{title}</h3>
      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id} className="rounded-md border bg-surface p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{r.canonical_name}</span>
              <Badge tone={tone[r.importance]}>{r.importance}</Badge>
              {r.category && <Badge>{titleCase(r.category)}</Badge>}
              {r.min_years !== null && <Badge tone="accent">{r.min_years}+ years</Badge>}
            </div>
            {r.evidence_snippet && <p className="mt-1.5 text-xs text-muted">“{r.evidence_snippet}”</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function JobDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const invalidate = useInvalidateAll();
  const { data: job, isLoading, isError, error, refetch } = useJob(id);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ title: "", company: "", location: "", raw_text: "" });
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (job) setForm({ title: job.title, company: job.company ?? "", location: job.location ?? "", raw_text: job.raw_text });
  }, [job]);

  const save = useMutation({
    mutationFn: () => jobsApi.update(id, { title: form.title, company: form.company, location: form.location, raw_text: form.raw_text }),
    onSuccess: async () => {
      await invalidate();
      setEditing(false);
      toast.success("Job description updated and re-parsed.");
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const remove = useDeleteMutation(jobsApi.remove, () => {
    toast.success("Job description deleted.");
    navigate("/app/jobs", { replace: true });
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !job) return <ErrorState error={error} onRetry={() => refetch()} />;

  const skills = job.requirements.filter((r) => r.kind === "skill");
  const other = (k: Requirement["kind"]) => job.requirements.filter((r) => r.kind === k);

  return (
    <div>
      <PageHeader
        title={job.title}
        description={[job.company, job.location].filter(Boolean).join(" · ") || undefined}
        actions={
          <>
            <Button asChild><Link to={`/app/analyze?job=${job.id}`}><Sparkles className="h-4 w-4" />Analyze a resume</Link></Button>
            <Button variant="secondary" onClick={() => setEditing((e) => !e)}><Pencil className="h-4 w-4" />{editing ? "Stop editing" : "Edit"}</Button>
            <Button variant="ghost" aria-label="Delete job description" onClick={() => setConfirmDelete(true)}><Trash2 className="h-4 w-4" /></Button>
          </>
        }
      />
      {job.source_url && (
        <p className="mb-4 text-sm text-muted">
          Imported from{" "}
          <a href={job.source_url} target="_blank" rel="noopener noreferrer nofollow" className="inline-flex items-center gap-1 text-accent hover:underline">
            {new URL(job.source_url).hostname}<ExternalLink className="h-3 w-3" aria-hidden />
          </a>
        </p>
      )}

      {editing && (
        <Card className="mb-6">
          <CardHeader title="Edit job description" description="Changing the text re-extracts requirements. Existing analyses keep their original results." />
          <CardBody className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-3">
              <Input aria-label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <Input aria-label="Company" placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              <Input aria-label="Location" placeholder="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
            </div>
            <Textarea aria-label="Job description text" className="min-h-[240px]" value={form.raw_text} onChange={(e) => setForm({ ...form, raw_text: e.target.value })} />
            <Button loading={save.isPending} disabled={form.raw_text.trim().length < 80} onClick={() => save.mutate()}>Save changes</Button>
          </CardBody>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title={`Extracted requirements (${job.requirements.length})`} description="What CareerLens understood from the description. Required vs preferred is inferred from the wording." />
          <CardBody className="space-y-5">
            {job.requirements.length === 0 && <p className="text-sm text-muted">No requirements could be extracted. Try pasting a more detailed description.</p>}
            <Group title="Skills & tools" items={skills} />
            <Group title="Responsibilities" items={other("responsibility")} />
            <Group title="Experience" items={other("experience")} />
            <Group title="Education" items={other("education")} />
            <Group title="Certifications" items={other("certification")} />
          </CardBody>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Original text" />
          <CardBody><pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap break-words font-sans text-sm text-muted">{job.raw_text}</pre></CardBody>
        </Card>
      </div>

      <ConfirmDialog open={confirmDelete} onOpenChange={setConfirmDelete} title="Delete this job description?" description="Analyses based on it will also be permanently deleted." confirmLabel="Delete" loading={remove.isPending} onConfirm={() => remove.mutate(id, { onError: (e) => toast.error(errorMessage(e)) })} />
    </div>
  );
}
