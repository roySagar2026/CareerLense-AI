import { z } from "zod";

export const passwordSchema = z
  .string()
  .min(10, "Use at least 10 characters")
  .max(128, "Use at most 128 characters")
  .refine((v) => /[A-Za-z]/.test(v), "Include at least one letter")
  .refine((v) => /\d/.test(v), "Include at least one number");

export const loginSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z
  .object({
    full_name: z.string().trim().max(120).optional(),
    email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
    password: passwordSchema,
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, { path: ["confirm"], message: "Passwords do not match" });

export const forgotSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
});

export const resetSchema = z
  .object({ password: passwordSchema, confirm: z.string() })
  .refine((d) => d.password === d.confirm, { path: ["confirm"], message: "Passwords do not match" });

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Enter your current password"),
    new_password: passwordSchema,
    confirm: z.string(),
  })
  .refine((d) => d.new_password === d.confirm, { path: ["confirm"], message: "Passwords do not match" });

export const jobPasteSchema = z.object({
  title: z.string().trim().max(200).optional(),
  company: z.string().trim().max(200).optional(),
  location: z.string().trim().max(200).optional(),
  raw_text: z
    .string()
    .trim()
    .min(80, "Paste at least 80 characters of the job description")
    .max(50000, "The job description is too long (50,000 characters max)"),
});

export const jobUrlSchema = z.object({
  url: z.string().trim().url("Enter a full URL starting with https://").refine((u) => /^https?:\/\//i.test(u), "Only http(s) links are supported"),
  title: z.string().trim().max(200).optional(),
  company: z.string().trim().max(200).optional(),
  location: z.string().trim().max(200).optional(),
});

export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

export function validateResumeFile(file: File): string | null {
  const ok = /\.(pdf|docx)$/i.test(file.name);
  if (!ok) return "Only PDF and DOCX files are supported.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_UPLOAD_BYTES) return "That file is larger than 4 MB.";
  return null;
}
