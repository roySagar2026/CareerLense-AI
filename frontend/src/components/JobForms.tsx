import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";
import { Link2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Field, Input, Textarea } from "@/components/ui/Field";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { useInvalidateAll } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { jobsApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import type { Job } from "@/types/api";
import { jobPasteSchema, jobUrlSchema } from "@/utils/validation";

type PasteValues = z.infer<typeof jobPasteSchema>;
type UrlValues = z.infer<typeof jobUrlSchema>;

export function JobForms({ onCreated }: { onCreated?: (job: Job) => void }) {
  const toast = useToast();
  const invalidate = useInvalidateAll();
  const [urlError, setUrlError] = useState<string | null>(null);
  const [tab, setTab] = useState("paste");
  const paste = useForm<PasteValues>({ resolver: zodResolver(jobPasteSchema) });
  const url = useForm<UrlValues>({ resolver: zodResolver(jobUrlSchema) });

  const created = async (job: Job) => {
    await invalidate();
    toast.success("Job description saved.");
    onCreated?.(job);
  };

  const onPaste = paste.handleSubmit(async (v) => {
    try {
      const job = await jobsApi.create({ ...v, title: v.title || undefined, company: v.company || undefined, location: v.location || undefined });
      paste.reset();
      await created(job);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  });

  const onUrl = url.handleSubmit(async (v) => {
    setUrlError(null);
    try {
      const job = await jobsApi.importUrl({ ...v, title: v.title || undefined, company: v.company || undefined, location: v.location || undefined });
      url.reset();
      await created(job);
    } catch (e) {
      setUrlError(errorMessage(e));
      setTab("url");
    }
  });

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList aria-label="How to add a job description">
        <TabsTrigger value="paste">Paste text</TabsTrigger>
        <TabsTrigger value="url">Import from link</TabsTrigger>
      </TabsList>
      <TabsContent value="paste">
        <form onSubmit={onPaste} className="space-y-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Job title">{(p) => <Input placeholder="Backend Engineer" {...p} {...paste.register("title")} />}</Field>
            <Field label="Company">{(p) => <Input placeholder="Acme Corp" {...p} {...paste.register("company")} />}</Field>
            <Field label="Location">{(p) => <Input placeholder="Remote" {...p} {...paste.register("location")} />}</Field>
          </div>
          <Field label="Job description" error={paste.formState.errors.raw_text?.message}>
            {(p) => <Textarea className="min-h-[220px]" placeholder="Paste the full job description here…" {...p} {...paste.register("raw_text")} />}
          </Field>
          <Button type="submit" loading={paste.formState.isSubmitting}>Save job description</Button>
        </form>
      </TabsContent>
      <TabsContent value="url">
        <form onSubmit={onUrl} className="space-y-4" noValidate>
          <Field label="Job posting URL" error={url.formState.errors.url?.message} hint="Public pages only. Some sites block automated access; if so, paste the text instead.">
            {(p) => <Input type="url" placeholder="https://company.com/careers/backend-engineer" {...p} {...url.register("url")} />}
          </Field>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Job title (optional)">{(p) => <Input {...p} {...url.register("title")} />}</Field>
            <Field label="Company (optional)">{(p) => <Input {...p} {...url.register("company")} />}</Field>
            <Field label="Location (optional)">{(p) => <Input {...p} {...url.register("location")} />}</Field>
          </div>
          {urlError && (
            <p role="alert" className="rounded-md border border-warning/30 bg-warning/10 p-3 text-sm">
              {urlError}{" "}
              <button type="button" className="underline" onClick={() => setTab("paste")}>Paste the text instead</button>
            </p>
          )}
          <Button type="submit" loading={url.formState.isSubmitting}><Link2 className="h-4 w-4" />Import</Button>
        </form>
      </TabsContent>
    </Tabs>
  );
}

