import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Settings2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Field, Input, Select } from "@/components/ui/Field";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { JobForms } from "@/components/JobForms";
import { useInvalidateAll, useJobs, useResumes } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { analysisApi } from "@/services/api";
import { errorCode, errorMessage } from "@/services/http";
import type { DimensionKey } from "@/types/api";

const DEFAULT_WEIGHTS: Record<DimensionKey, number> = {
  required_skills: 35,
  preferred_skills: 15,
  experience: 20,
  responsibilities: 15,
  education: 10,
  structure: 5,
};
const LABELS: Record<DimensionKey, string> = {
  required_skills: "Required skills",
  preferred_skills: "Preferred skills",
  experience: "Experience",
  responsibilities: "Responsibilities",
  education: "Education & certifications",
  structure: "Structure & readability",
};

export default function NewAnalysis() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const invalidate = useInvalidateAll();
  const resumes = useResumes();
  const jobs = useJobs();
  const [resumeId, setResumeId] = useState(params.get("resume") ?? "");
  const [jobId, setJobId] = useState(params.get("job") ?? "");
  const [showWeights, setShowWeights] = useState(false);
  const [weights, setWeights] = useState<Record<DimensionKey, number>>({ ...DEFAULT_WEIGHTS });
  const [addingJob, setAddingJob] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const readyResumes = (resumes.data?.items ?? []).filter((r) => r.status === "ready");
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const customised = (Object.keys(DEFAULT_WEIGHTS) as DimensionKey[]).some((k) => weights[k] !== DEFAULT_WEIGHTS[k]);

  const run = useMutation({
    mutationFn: () =>
      analysisApi.create({ resume_id: resumeId, job_id: jobId, scoring_weights: customised ? weights : undefined }),
    onSuccess: async (a) => {
      await invalidate();
      toast.success("Analysis complete.");
      navigate(`/app/analysis/${a.id}`);
    },
    onError: (e) =>
      setProblem(
        errorCode(e) === "no_requirements"
          ? "No requirements could be extracted from that job description. Edit it to include a fuller list of skills and responsibilities."
          : errorMessage(e),
      ),
  });

  if (resumes.isLoading || jobs.isLoading) return <Skeleton className="h-64" />;
  if (resumes.isError) return <ErrorState error={resumes.error} onRetry={() => resumes.refetch()} />;
  if (jobs.isError) return <ErrorState error={jobs.error} onRetry={() => jobs.refetch()} />;

  if (readyResumes.length === 0) {
    return (
      <div>
        <PageHeader title="New analysis" />
        <EmptyState icon={Sparkles} title="Upload a resume first" description="You need at least one successfully parsed resume to run an analysis." action={<Button asChild><Link to="/app/resumes">Upload a resume</Link></Button>} />
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <PageHeader title="New analysis" description="Compare one resume against one job description." />
      <Card>
        <CardBody className="space-y-5">
          <Field label="Resume">
            {(p) => (
              <Select {...p} value={resumeId} onChange={(e) => { setResumeId(e.target.value); setProblem(null); }}>
                <option value="">Select a resume…</option>
                {readyResumes.map((r) => <option key={r.id} value={r.id}>{r.name} (v{r.version})</option>)}
              </Select>
            )}
          </Field>
          <Field label="Job description">
            {(p) => (
              <Select {...p} value={jobId} onChange={(e) => { setJobId(e.target.value); setProblem(null); }}>
                <option value="">Select a job description…</option>
                {(jobs.data?.items ?? []).map((j) => <option key={j.id} value={j.id}>{j.title}{j.company ? ` · ${j.company}` : ""}</option>)}
              </Select>
            )}
          </Field>
          <button type="button" className="text-sm text-accent hover:underline" onClick={() => setAddingJob((v) => !v)}>
            {addingJob ? "Hide new job form" : "+ Add a new job description"}
          </button>
          {addingJob && (
            <div className="rounded-lg border bg-surface p-4">
              <JobForms onCreated={(j) => { setJobId(j.id); setAddingJob(false); }} />
            </div>
          )}

          <div className="border-t pt-4">
            <button type="button" className="flex items-center gap-2 text-sm font-medium" aria-expanded={showWeights} onClick={() => setShowWeights((v) => !v)}>
              <Settings2 className="h-4 w-4" aria-hidden />Scoring weights {customised && <span className="text-xs text-warning">(customised)</span>}
            </button>
            {showWeights && (
              <div className="mt-3 space-y-3">
                <p className="text-xs text-muted">Weights are relative: they're normalised to 100%, and dimensions that don't apply to the job are redistributed. Defaults are our own starting point, not an industry standard.</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {(Object.keys(DEFAULT_WEIGHTS) as DimensionKey[]).map((k) => (
                    <div key={k}>
                      <label htmlFor={`w-${k}`} className="mb-1 block text-xs text-muted">{LABELS[k]}</label>
                      <Input id={`w-${k}`} type="number" min={0} max={100} value={weights[k]} onChange={(e) => setWeights({ ...weights, [k]: Math.max(0, Math.min(100, Number(e.target.value) || 0)) })} />
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-3 text-xs text-muted">
                  <span>Total: {total}</span>
                  <Button variant="ghost" size="sm" onClick={() => setWeights({ ...DEFAULT_WEIGHTS })}>Reset to defaults</Button>
                </div>
                {total === 0 && <p role="alert" className="text-xs text-danger">At least one weight must be above zero.</p>}
              </div>
            )}
          </div>

          {problem && <p role="alert" className="rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger">{problem}</p>}
          <Button size="lg" disabled={!resumeId || !jobId || total === 0} loading={run.isPending} onClick={() => { setProblem(null); run.mutate(); }}>
            <Sparkles className="h-4 w-4" />Run analysis
          </Button>
          <p className="text-xs text-muted">The result is a heuristic alignment estimate, not an employer ATS score.</p>
        </CardBody>
      </Card>
    </div>
  );
}
