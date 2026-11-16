import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Download, Pencil, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Select, Textarea } from "@/components/ui/Field";
import { ErrorState } from "@/components/ui/States";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { ResumeUploader } from "@/components/ResumeUploader";
import { keys, useDeleteMutation, useInvalidateAll, useResume, useVersions } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { resumesApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { EvidenceLevel, ResumeDetail as ResumeDetailType, ResumeSection, SectionType } from "@/types/api";
import { formatBytes, formatDate, titleCase } from "@/utils/format";

const SECTION_TYPES: SectionType[] = ["summary", "skills", "experience", "projects", "education", "certifications", "achievements", "contact", "other"];
const evidenceTone: Record<EvidenceLevel, BadgeTone> = { demonstrated: "success", listed: "primary", mentioned: "warning" };
const evidenceHelp: Record<EvidenceLevel, string> = {
  demonstrated: "Used in a described project or role",
  listed: "Appears in a skills list",
  mentioned: "Mentioned without supporting detail",
};

function SectionCard({ resumeId, section }: { resumeId: string; section: ResumeSection }) {
  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState(section.content);
  const [type, setType] = useState<SectionType>(section.section_type);
  const qc = useQueryClient();
  const toast = useToast();
  const save = useMutation({
    mutationFn: () => resumesApi.updateSection(resumeId, section.id, { content, section_type: type }),
    onSuccess: (data) => {
      qc.setQueryData(keys.resume(resumeId), data);
      toast.success("Section updated. Skills were recomputed.");
      setEditing(false);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <Card>
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-medium">{titleCase(section.section_type)}</h3>
          {section.heading_text && <span className="text-xs text-muted">“{section.heading_text}”</span>}
          {section.user_edited && <Badge tone="accent">Edited by you</Badge>}
          {section.confidence < 0.6 && <Badge tone="warning">Low confidence</Badge>}
        </div>
        {!editing && (
          <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="h-3.5 w-3.5" />
            Correct
          </Button>
        )}
      </div>
      <CardBody>
        {editing ? (
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-muted" htmlFor={`type-${section.id}`}>Section type</label>
              <Select id={`type-${section.id}`} value={type} onChange={(e) => setType(e.target.value as SectionType)} className="max-w-xs">
                {SECTION_TYPES.map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}
              </Select>
            </div>
            <Textarea aria-label={`${titleCase(section.section_type)} content`} className="min-h-[200px] font-mono text-xs" value={content} onChange={(e) => setContent(e.target.value)} />
            <div className="flex gap-2">
              <Button size="sm" loading={save.isPending} onClick={() => save.mutate()}>Save changes</Button>
              <Button size="sm" variant="secondary" onClick={() => { setEditing(false); setContent(section.content); setType(section.section_type); }}>Cancel</Button>
            </div>
          </div>
        ) : (
          <pre className="whitespace-pre-wrap break-words font-sans text-sm text-foreground/90">{section.content || "(empty)"}</pre>
        )}
      </CardBody>
    </Card>
  );
}

function OriginalFile({ resume }: { resume: ResumeDetailType }) {
  const isPdf = resume.mime_type === "application/pdf";
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["resume-file", resume.id],
    queryFn: () => resumesApi.file(resume.id),
    enabled: resume.has_original_file,
    staleTime: Infinity,
    gcTime: 0,
  });
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!data) return;
    const u = URL.createObjectURL(data);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [data]);

  if (!resume.has_original_file) {
    return <p className="text-sm text-muted">The original file isn't stored (it was removed, or your privacy settings disable storing originals). The extracted text is still available.</p>;
  }
  if (isLoading) return <p className="text-sm text-muted">Loading file…</p>;
  if (isError) return <ErrorState error={error} />;
  return (
    <div className="space-y-3">
      {url && (
        <Button asChild variant="secondary" size="sm">
          <a href={url} download={resume.original_filename}><Download className="h-4 w-4" />Download {resume.original_filename}</a>
        </Button>
      )}
      {isPdf && url ? (
        <iframe title="Resume preview" src={url} className="h-[70vh] w-full rounded-md border bg-white" />
      ) : (
        <p className="text-sm text-muted">Previews are available for PDF files. Download the DOCX to view it in Word, or see the extracted text in the other tabs.</p>
      )}
    </div>
  );
}

export default function ResumeDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const invalidate = useInvalidateAll();
  const { data: resume, isLoading, isError, error, refetch } = useResume(id);
  const versions = useVersions(id);
  const [renaming, setRenaming] = useState(false);
  const [name, setName] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmReprocess, setConfirmReprocess] = useState(false);

  const rename = useMutation({
    mutationFn: (n: string) => resumesApi.rename(id, n),
    onSuccess: async () => {
      await invalidate();
      setRenaming(false);
      toast.success("Resume renamed.");
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const reprocess = useMutation({
    mutationFn: () => resumesApi.reprocess(id),
    onSuccess: async () => {
      await invalidate();
      setConfirmReprocess(false);
      toast.success("Resume reprocessed.");
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const remove = useDeleteMutation(resumesApi.remove, () => {
    toast.success("Resume deleted.");
    navigate("/app/resumes", { replace: true });
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !resume) return <ErrorState error={error} onRetry={() => refetch()} />;

  return (
    <div>
      <PageHeader
        title={resume.name}
        description={`${resume.original_filename} · ${formatBytes(resume.size_bytes)} · version ${resume.version} · uploaded ${formatDate(resume.created_at)}`}
        actions={
          <>
            <Button asChild><Link to={`/app/analyze?resume=${resume.id}`}><Sparkles className="h-4 w-4" />Analyze</Link></Button>
            <Button variant="secondary" onClick={() => { setName(resume.name); setRenaming(true); }}><Pencil className="h-4 w-4" />Rename</Button>
            {resume.has_original_file && <Button variant="secondary" onClick={() => setConfirmReprocess(true)}><RefreshCw className="h-4 w-4" />Reprocess</Button>}
            <Button variant="ghost" onClick={() => setConfirmDelete(true)} aria-label="Delete resume"><Trash2 className="h-4 w-4" /></Button>
          </>
        }
      />

      {renaming && (
        <form className="mb-4 flex max-w-md gap-2" onSubmit={(e) => { e.preventDefault(); if (name.trim()) rename.mutate(name.trim()); }}>
          <Input aria-label="Resume name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoFocus />
          <Button type="submit" loading={rename.isPending}>Save</Button>
          <Button type="button" variant="secondary" onClick={() => setRenaming(false)}>Cancel</Button>
        </form>
      )}

      <div className="mb-5 flex flex-wrap items-center gap-2">
        {resume.status === "failed" ? <Badge tone="danger">Extraction failed</Badge> : <Badge tone="success">Parsed</Badge>}
        {resume.extraction_method && <Badge>Method: {resume.extraction_method}</Badge>}
        {resume.extraction_confidence !== null && <Badge tone={resume.extraction_confidence >= 0.7 ? "success" : "warning"}>Extraction confidence {Math.round(resume.extraction_confidence * 100)}%</Badge>}
        {resume.page_count !== null && <Badge>{resume.page_count} page{resume.page_count === 1 ? "" : "s"}</Badge>}
        <Badge>{resume.word_count} words</Badge>
      </div>

      {resume.error_message && (
        <div role="alert" className="mb-5 flex gap-3 rounded-lg border border-danger/30 bg-danger/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" aria-hidden />
          <p>{resume.error_message}</p>
        </div>
      )}
      {resume.warnings.length > 0 && (
        <div className="mb-5 rounded-lg border border-warning/30 bg-warning/10 p-4 text-sm">
          <p className="mb-1 font-medium">Extraction notes</p>
          <ul className="list-inside list-disc space-y-0.5 text-muted">{resume.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      )}

      <Tabs defaultValue="sections">
        <TabsList aria-label="Resume details">
          <TabsTrigger value="sections">Sections ({resume.sections.length})</TabsTrigger>
          <TabsTrigger value="skills">Skills ({resume.skills.length})</TabsTrigger>
          <TabsTrigger value="parsed">Structured data</TabsTrigger>
          <TabsTrigger value="text">Raw text</TabsTrigger>
          <TabsTrigger value="original">Original file</TabsTrigger>
          <TabsTrigger value="versions">Versions</TabsTrigger>
        </TabsList>

        <TabsContent value="sections" className="space-y-4">
          <p className="text-sm text-muted">If a section was detected incorrectly, correct it. Skills and structured data are recomputed from your edits.</p>
          {resume.sections.length === 0 ? <p className="text-sm text-muted">No sections were detected.</p> : resume.sections.map((s) => <SectionCard key={s.id} resumeId={resume.id} section={s} />)}
        </TabsContent>

        <TabsContent value="skills">
          <div className="mb-3 flex flex-wrap gap-3 text-xs text-muted">
            {(Object.keys(evidenceHelp) as EvidenceLevel[]).map((k) => <span key={k}><Badge tone={evidenceTone[k]}>{k}</Badge> {evidenceHelp[k]}</span>)}
          </div>
          {resume.skills.length === 0 ? <p className="text-sm text-muted">No skills were recognised.</p> : (
            <Card className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead className="border-b text-left text-xs text-muted"><tr><th className="px-4 py-2">Skill</th><th className="px-4 py-2">Category</th><th className="px-4 py-2">Evidence</th><th className="px-4 py-2">Found in</th><th className="px-4 py-2 text-right">Mentions</th></tr></thead>
                <tbody className="divide-y">
                  {resume.skills.map((s) => (
                    <tr key={s.id}>
                      <td className="px-4 py-2 font-medium">{s.canonical_name}</td>
                      <td className="px-4 py-2 text-muted">{titleCase(s.category)}</td>
                      <td className="px-4 py-2"><Badge tone={evidenceTone[s.evidence_level]}>{s.evidence_level}</Badge></td>
                      <td className="px-4 py-2 text-muted">{s.section_type ? titleCase(s.section_type) : "—"}</td>
                      <td className="px-4 py-2 text-right tabular-nums">{s.occurrences}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="parsed" className="grid gap-4 md:grid-cols-2">
          <Card><CardBody>
            <h3 className="mb-2 font-medium">Contact</h3>
            <dl className="space-y-1 text-sm">
              <div className="flex gap-2"><dt className="w-16 text-muted">Name</dt><dd>{resume.parsed_data.contact.name ?? "—"}</dd></div>
              <div className="flex gap-2"><dt className="w-16 text-muted">Email</dt><dd className="break-all">{resume.parsed_data.contact.email ?? "—"}</dd></div>
              <div className="flex gap-2"><dt className="w-16 text-muted">Phone</dt><dd>{resume.parsed_data.contact.phone ?? "—"}</dd></div>
              <div className="flex gap-2"><dt className="w-16 text-muted">Links</dt><dd className="break-all">{resume.parsed_data.contact.links.join(", ") || "—"}</dd></div>
            </dl>
            <p className="mt-3 text-sm text-muted">Estimated experience: {resume.parsed_data.estimated_years_experience} years</p>
          </CardBody></Card>
          <Card><CardBody>
            <h3 className="mb-2 font-medium">Education</h3>
            {resume.parsed_data.education.length === 0 ? <p className="text-sm text-muted">None detected.</p> : (
              <ul className="space-y-2 text-sm">{resume.parsed_data.education.map((e, i) => <li key={i}>{[e.degree, e.institution, e.year].filter(Boolean).join(" · ")}</li>)}</ul>
            )}
            <h3 className="mb-2 mt-4 font-medium">Certifications</h3>
            {resume.parsed_data.certifications.length === 0 ? <p className="text-sm text-muted">None detected.</p> : <ul className="list-inside list-disc text-sm">{resume.parsed_data.certifications.map((c) => <li key={c}>{c}</li>)}</ul>}
          </CardBody></Card>
          <Card className="md:col-span-2"><CardBody>
            <h3 className="mb-2 font-medium">Experience</h3>
            {resume.parsed_data.experience.length === 0 ? <p className="text-sm text-muted">None detected.</p> : (
              <ul className="space-y-4 text-sm">{resume.parsed_data.experience.map((x, i) => (
                <li key={i}><p className="font-medium">{[x.title, x.organization].filter(Boolean).join(" · ") || "Untitled role"}{x.date_range && <span className="ml-2 font-normal text-muted">{x.date_range}</span>}</p>
                  <ul className="mt-1 list-inside list-disc text-muted">{x.bullets.map((b, j) => <li key={j}>{b}</li>)}</ul></li>
              ))}</ul>
            )}
            <h3 className="mb-2 mt-5 font-medium">Projects</h3>
            {resume.parsed_data.projects.length === 0 ? <p className="text-sm text-muted">None detected.</p> : (
              <ul className="space-y-4 text-sm">{resume.parsed_data.projects.map((p, i) => (
                <li key={i}><p className="font-medium">{p.name}</p>
                  {p.tech.length > 0 && <div className="mt-1 flex flex-wrap gap-1">{p.tech.map((t) => <Badge key={t}>{t}</Badge>)}</div>}
                  <ul className="mt-1 list-inside list-disc text-muted">{p.bullets.map((b, j) => <li key={j}>{b}</li>)}</ul></li>
              ))}</ul>
            )}
          </CardBody></Card>
        </TabsContent>

        <TabsContent value="text"><Card><CardBody><pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-muted">{resume.raw_text || "(no text extracted)"}</pre></CardBody></Card></TabsContent>
        <TabsContent value="original"><OriginalFile resume={resume} /></TabsContent>

        <TabsContent value="versions" className="space-y-5">
          <ul className="space-y-2">
            {(versions.data ?? []).map((v) => (
              <li key={v.id}>
                <Link to={`/app/resumes/${v.id}`} className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 text-sm hover:bg-surface">
                  <span>Version {v.version} · {v.original_filename}</span>
                  <span className="flex items-center gap-2 text-xs text-muted">{formatDate(v.created_at)}{v.id === resume.id && <Badge tone="primary">Viewing</Badge>}</span>
                </Link>
              </li>
            ))}
          </ul>
          <div>
            <h3 className="mb-2 text-sm font-medium">Upload a new version of this resume</h3>
            <ResumeUploader parentResumeId={resume.id} compact />
          </div>
        </TabsContent>
      </Tabs>

      <ConfirmDialog open={confirmDelete} onOpenChange={setConfirmDelete} title="Delete this resume?" description="The resume and all analyses that used it will be permanently deleted." confirmLabel="Delete resume" loading={remove.isPending} onConfirm={() => remove.mutate(id, { onError: (e) => toast.error(errorMessage(e)) })} />
      <ConfirmDialog open={confirmReprocess} onOpenChange={setConfirmReprocess} title="Reprocess this resume?" description="The original file is parsed again. Any manual section corrections will be discarded." confirmLabel="Reprocess" destructive={false} loading={reprocess.isPending} onConfirm={() => reprocess.mutate()} />
    </div>
  );
}
