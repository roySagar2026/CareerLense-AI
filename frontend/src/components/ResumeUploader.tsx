import { useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, Loader2 } from "lucide-react";
import { resumesApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import { useToast } from "@/contexts/ToastContext";
import { useInvalidateAll } from "@/hooks/useQueries";
import { validateResumeFile } from "@/utils/validation";
import { cn } from "@/utils/cn";

export function ResumeUploader({ parentResumeId, compact }: { parentResumeId?: string; compact?: boolean }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const navigate = useNavigate();
  const invalidate = useInvalidateAll();
  const busy = progress !== null;

  const upload = async (file: File | undefined) => {
    if (!file) return;
    const problem = validateResumeFile(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setProgress(0);
    try {
      const resume = await resumesApi.upload(file, {
        parentResumeId,
        name: parentResumeId ? undefined : file.name.replace(/\.(pdf|docx)$/i, ""),
        onProgress: setProgress,
      });
      await invalidate();
      if (resume.status === "failed") {
        toast.error(resume.error_message ?? "The resume was uploaded but could not be read.");
      } else {
        toast.success("Resume uploaded and parsed.");
      }
      navigate(`/app/resumes/${resume.id}`);
    } catch (e) {
      setError(errorMessage(e, "Upload failed."));
    } finally {
      setProgress(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!busy) void upload(e.dataTransfer.files[0]);
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center rounded-lg border-2 border-dashed px-6 text-center transition-colors",
          compact ? "py-6" : "py-10",
          dragging ? "border-primary bg-primary/10" : "bg-card/50",
        )}
      >
        {busy ? <Loader2 className="h-7 w-7 animate-spin text-primary" aria-hidden /> : <FileUp className="h-7 w-7 text-primary" aria-hidden />}
        <p className="mt-3 text-sm font-medium">
          {busy ? (progress === 100 ? "Analyzing document…" : `Uploading… ${progress}%`) : parentResumeId ? "Drop the new version here" : "Drag and drop your resume here"}
        </p>
        <p className="mt-1 text-xs text-muted">PDF or DOCX, up to 4 MB</p>
        <button
          type="button"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
          className="mt-4 rounded-md border bg-surface px-4 py-2 text-sm font-medium hover:bg-card disabled:opacity-50"
        >
          Choose file
        </button>
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          aria-label="Resume file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(e) => void upload(e.target.files?.[0])}
        />
        {busy && progress !== null && (
          <div className="mt-4 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-border" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
