import { http } from "./http";
import type {
  ActivityItem,
  AnalysisDetail,
  AnalysisSummary,
  AuthResponse,
  Comparison,
  DashboardSummary,
  DimensionKey,
  Job,
  JobDetail,
  KeywordMatch,
  Page,
  Recommendation,
  Resume,
  ResumeDetail,
  ResumeSection,
  SectionType,
  TrendPoint,
  User,
  PrivacySettings,
} from "@/types/api";

type Params = Record<string, string | number | boolean | undefined | null>;
const clean = (params?: Params): Params | undefined =>
  params
    ? Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""))
    : undefined;

export const authApi = {
  register: (body: { email: string; password: string; full_name?: string }) =>
    http.post<AuthResponse>("/auth/register", body).then((r) => r.data),
  login: (body: { email: string; password: string }) =>
    http.post<AuthResponse>("/auth/login", body).then((r) => r.data),
  forgotPassword: (email: string) =>
    http.post<{ message: string }>("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (body: { token: string; new_password: string }) =>
    http.post<{ message: string }>("/auth/reset-password", body).then((r) => r.data),
};

export const usersApi = {
  me: () => http.get<User>("/users/me").then((r) => r.data),
  update: (body: {
    full_name?: string | null;
    headline?: string | null;
    privacy_settings?: Partial<PrivacySettings>;
  }) => http.patch<User>("/users/me", body).then((r) => r.data),
  changePassword: (body: { current_password: string; new_password: string }) =>
    http.post("/users/me/password", body).then(() => undefined),
  deleteData: () => http.delete("/users/me/data").then(() => undefined),
  deleteAccount: (password: string) =>
    http.delete("/users/me", { data: { password } }).then(() => undefined),
};

export const resumesApi = {
  list: (params?: { search?: string; page?: number; page_size?: number }) =>
    http.get<Page<Resume>>("/resumes", { params: clean(params) }).then((r) => r.data),
  get: (id: string) => http.get<ResumeDetail>(`/resumes/${id}`).then((r) => r.data),
  upload: (
    file: File,
    opts: { name?: string; parentResumeId?: string; onProgress?: (percent: number) => void } = {},
  ) => {
    const form = new FormData();
    form.append("file", file);
    if (opts.name) form.append("name", opts.name);
    if (opts.parentResumeId) form.append("parent_resume_id", opts.parentResumeId);
    return http
      .post<ResumeDetail>("/resumes/upload", form, {
        timeout: 120_000,
        onUploadProgress: (e) => {
          if (e.total && opts.onProgress) opts.onProgress(Math.round((e.loaded / e.total) * 100));
        },
      })
      .then((r) => r.data);
  },
  rename: (id: string, name: string) => http.patch<Resume>(`/resumes/${id}`, { name }).then((r) => r.data),
  updateSection: (
    id: string,
    sectionId: string,
    body: { section_type?: SectionType; heading_text?: string | null; content?: string },
  ) => http.patch<ResumeDetail>(`/resumes/${id}/sections/${sectionId}`, body).then((r) => r.data),
  reprocess: (id: string) => http.post<ResumeDetail>(`/resumes/${id}/reprocess`).then((r) => r.data),
  versions: (id: string) => http.get<Resume[]>(`/resumes/${id}/versions`).then((r) => r.data),
  file: (id: string) => http.get<Blob>(`/resumes/${id}/file`, { responseType: "blob" }).then((r) => r.data),
  remove: (id: string) => http.delete(`/resumes/${id}`).then(() => undefined),
};

export interface JobInput {
  title?: string;
  company?: string;
  location?: string;
  raw_text?: string;
}

export const jobsApi = {
  list: (params?: { search?: string; page?: number; page_size?: number }) =>
    http.get<Page<Job>>("/jobs", { params: clean(params) }).then((r) => r.data),
  get: (id: string) => http.get<JobDetail>(`/jobs/${id}`).then((r) => r.data),
  create: (body: JobInput & { raw_text: string }) => http.post<JobDetail>("/jobs", body).then((r) => r.data),
  importUrl: (body: { url: string; title?: string; company?: string; location?: string }) =>
    http.post<JobDetail>("/jobs/import-url", body).then((r) => r.data),
  update: (id: string, body: JobInput) => http.patch<JobDetail>(`/jobs/${id}`, body).then((r) => r.data),
  remove: (id: string) => http.delete(`/jobs/${id}`).then(() => undefined),
};

export interface AnalysisFilters {
  company?: string;
  job_title?: string;
  resume_id?: string;
  job_id?: string;
  page?: number;
  page_size?: number;
}

export interface KeywordFilters {
  result_category?: string;
  kind?: string;
  importance?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const analysisApi = {
  create: (body: {
    resume_id: string;
    job_id: string;
    scoring_weights?: Partial<Record<DimensionKey, number>>;
  }) => http.post<AnalysisDetail>("/analysis", body).then((r) => r.data),
  list: (params?: AnalysisFilters) =>
    http.get<Page<AnalysisSummary>>("/analysis", { params: clean(params as Params) }).then((r) => r.data),
  get: (id: string) => http.get<AnalysisDetail>(`/analysis/${id}`).then((r) => r.data),
  remove: (id: string) => http.delete(`/analysis/${id}`).then(() => undefined),
  keywords: (id: string, params?: KeywordFilters) =>
    http.get<Page<KeywordMatch>>(`/analysis/${id}/keywords`, { params: clean(params as Params) }).then((r) => r.data),
  recommendations: (id: string, params?: { priority?: string; section_type?: string }) =>
    http.get<Recommendation[]>(`/analysis/${id}/recommendations`, { params: clean(params) }).then((r) => r.data),
  compare: (a: string, b: string) => http.get<Comparison>("/analysis/compare", { params: { a, b } }).then((r) => r.data),
  trend: (jobId: string) => http.get<TrendPoint[]>("/analysis/trend", { params: { job_id: jobId } }).then((r) => r.data),
};

export const dashboardApi = {
  summary: () => http.get<DashboardSummary>("/dashboard/summary").then((r) => r.data),
  activity: (limit = 10) => http.get<ActivityItem[]>("/dashboard/recent-activity", { params: { limit } }).then((r) => r.data),
};

export type { ResumeSection };
