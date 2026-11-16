import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analysisApi, dashboardApi, jobsApi, resumesApi, type AnalysisFilters, type KeywordFilters } from "@/services/api";

export const keys = {
  dashboard: ["dashboard"] as const,
  resumes: (search?: string) => ["resumes", search ?? ""] as const,
  resume: (id: string) => ["resume", id] as const,
  versions: (id: string) => ["resume-versions", id] as const,
  jobs: (search?: string) => ["jobs", search ?? ""] as const,
  job: (id: string) => ["job", id] as const,
  analyses: (f: AnalysisFilters) => ["analyses", f] as const,
  analysis: (id: string) => ["analysis", id] as const,
  keywords: (id: string, f: KeywordFilters) => ["keywords", id, f] as const,
  recs: (id: string, priority?: string) => ["recs", id, priority ?? ""] as const,
};

export const useDashboard = () => useQuery({ queryKey: keys.dashboard, queryFn: dashboardApi.summary });
export const useActivity = () => useQuery({ queryKey: ["activity"], queryFn: () => dashboardApi.activity(8) });
export const useResumes = (search?: string) =>
  useQuery({ queryKey: keys.resumes(search), queryFn: () => resumesApi.list({ search, page_size: 100 }), placeholderData: keepPreviousData });
export const useResume = (id: string) => useQuery({ queryKey: keys.resume(id), queryFn: () => resumesApi.get(id), enabled: Boolean(id) });
export const useVersions = (id: string) => useQuery({ queryKey: keys.versions(id), queryFn: () => resumesApi.versions(id), enabled: Boolean(id) });
export const useJobs = (search?: string) =>
  useQuery({ queryKey: keys.jobs(search), queryFn: () => jobsApi.list({ search, page_size: 100 }), placeholderData: keepPreviousData });
export const useJob = (id: string) => useQuery({ queryKey: keys.job(id), queryFn: () => jobsApi.get(id), enabled: Boolean(id) });
export const useAnalyses = (filters: AnalysisFilters) =>
  useQuery({ queryKey: keys.analyses(filters), queryFn: () => analysisApi.list(filters), placeholderData: keepPreviousData });
export const useAnalysis = (id: string) => useQuery({ queryKey: keys.analysis(id), queryFn: () => analysisApi.get(id), enabled: Boolean(id) });
export const useKeywords = (id: string, filters: KeywordFilters) =>
  useQuery({ queryKey: keys.keywords(id, filters), queryFn: () => analysisApi.keywords(id, filters), enabled: Boolean(id), placeholderData: keepPreviousData });
export const useRecommendations = (id: string, priority?: string) =>
  useQuery({ queryKey: keys.recs(id, priority), queryFn: () => analysisApi.recommendations(id, { priority }), enabled: Boolean(id) });

/** Invalidate everything that can change when resumes/jobs/analyses are created or removed. */
export function useInvalidateAll() {
  const qc = useQueryClient();
  return () =>
    Promise.all(
      ["dashboard", "activity", "resumes", "resume", "resume-versions", "jobs", "job", "analyses", "analysis"].map((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      ),
    );
}

export function useDeleteMutation(fn: (id: string) => Promise<void>, onDone?: () => void) {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: fn,
    onSuccess: async () => {
      await invalidate();
      onDone?.();
    },
  });
}
