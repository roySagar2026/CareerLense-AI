import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

// Full user journey against a running app (frontend + API + database).
// Uses only the synthetic fixtures in ./fixtures, never real candidate documents.

const resumePath = path.join(__dirname, "fixtures", "synthetic_resume.docx");
const jobText = readFileSync(path.join(__dirname, "fixtures", "synthetic_job.txt"), "utf8");
const password = "CareerLens-E2E-9";

test("register → upload → analyze → review → history → delete", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  // 1–2. Register (also logs in), then prove login works after a logout.
  await page.goto("/");
  await page.getByRole("link", { name: "Get started" }).click();
  await page.getByLabel("Full name (optional)").fill("E2E Tester");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password").fill(password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: /Welcome, E2E/ })).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).first().click();
  await expect(page).toHaveURL(/\/login/);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: /Welcome/ })).toBeVisible();

  // 3. Upload resume
  await page.getByRole("link", { name: "Resumes" }).first().click();
  await page.getByLabel("Resume file").setInputFiles(resumePath);
  await expect(page.getByText("Parsed")).toBeVisible();
  await expect(page.getByRole("tab", { name: /Skills \(/ })).toBeVisible();
  await page.getByRole("tab", { name: /Skills \(/ }).click();
  await expect(page.getByRole("cell", { name: "Python", exact: true })).toBeVisible();

  // 4. Submit job description
  await page.getByRole("link", { name: "Job descriptions" }).first().click();
  await page.getByLabel("Job title").fill("Backend Engineer");
  await page.getByLabel("Company").fill("Northwind");
  await page.getByLabel("Job description").fill(jobText);
  await page.getByRole("button", { name: "Save job description" }).click();
  await expect(page.getByText(/Extracted requirements/)).toBeVisible();

  // 5–6. Run analysis and view score
  await page.getByRole("link", { name: "New analysis" }).first().click();
  await page.getByLabel("Resume", { exact: true }).selectOption({ index: 1 });
  await page.getByLabel("Job description").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByRole("note")).toContainText("NOT the score");
  await expect(page.getByRole("img", { name: /Overall alignment score: \d+ out of 100/ })).toBeVisible();

  // 7. Matched and missing keywords
  await page.getByRole("tab", { name: "Keywords" }).click();
  await page.getByRole("button", { name: /Exact match/ }).click();
  await expect(page.getByRole("cell", { name: /Python/ }).first()).toBeVisible();
  await page.getByRole("button", { name: /Missing \(required\)/ }).click();
  await expect(page.getByRole("cell", { name: /Docker/ }).first()).toBeVisible();

  // 8. Recommendations are labelled as suggestions
  await page.getByRole("tab", { name: "Recommendations" }).click();
  await expect(page.getByText("Suggestion").first()).toBeVisible();
  await expect(page.getByText(/not facts about you/)).toBeVisible();

  // 9. Reopen from history
  await page.getByRole("link", { name: "History" }).first().click();
  await page.getByRole("link", { name: /Backend Engineer · Northwind/ }).click();
  await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();

  // 10. Delete the resume (cascades to the analysis)
  await page.getByRole("link", { name: "Resumes" }).first().click();
  await page.getByRole("button", { name: /^Delete / }).first().click();
  await page.getByRole("button", { name: "Delete resume" }).click();
  await expect(page.getByText("No resumes yet")).toBeVisible();
  await page.getByRole("link", { name: "History" }).first().click();
  await expect(page.getByText("No analyses yet")).toBeVisible();
});
