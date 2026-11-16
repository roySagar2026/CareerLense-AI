import { describe, expect, it } from "vitest";
import { jobPasteSchema, jobUrlSchema, loginSchema, passwordSchema, registerSchema, validateResumeFile } from "./validation";

describe("password rules", () => {
  it.each([
    ["short1", false],
    ["longpasswordwithoutdigits", false],
    ["1234567890123", false],
    ["CareerLens-Test-9", true],
  ])("%s -> %s", (value, ok) => {
    expect(passwordSchema.safeParse(value).success).toBe(ok);
  });
});

describe("forms", () => {
  it("rejects invalid login input", () => {
    expect(loginSchema.safeParse({ email: "nope", password: "x" }).success).toBe(false);
    expect(loginSchema.safeParse({ email: "a@b.co", password: "x" }).success).toBe(true);
  });

  it("requires matching passwords on register", () => {
    const base = { email: "a@b.co", password: "CareerLens-Test-9" };
    expect(registerSchema.safeParse({ ...base, confirm: "different1234" }).success).toBe(false);
    expect(registerSchema.safeParse({ ...base, confirm: base.password }).success).toBe(true);
  });

  it("enforces job description length and URL scheme", () => {
    expect(jobPasteSchema.safeParse({ raw_text: "too short" }).success).toBe(false);
    expect(jobPasteSchema.safeParse({ raw_text: "x".repeat(100) }).success).toBe(true);
    expect(jobUrlSchema.safeParse({ url: "ftp://example.com/job" }).success).toBe(false);
    expect(jobUrlSchema.safeParse({ url: "https://example.com/job" }).success).toBe(true);
  });
});

describe("validateResumeFile", () => {
  const file = (name: string, size: number) => new File([new Uint8Array(size)], name);
  it("accepts pdf and docx within the limit", () => {
    expect(validateResumeFile(file("cv.pdf", 10))).toBeNull();
    expect(validateResumeFile(file("cv.DOCX", 10))).toBeNull();
  });
  it("rejects other types, empty and oversized files", () => {
    expect(validateResumeFile(file("cv.exe", 10))).toMatch(/PDF and DOCX/);
    expect(validateResumeFile(file("cv.pdf", 0))).toMatch(/empty/);
    expect(validateResumeFile(file("cv.pdf", 5 * 1024 * 1024))).toMatch(/4 MB/);
  });
});
