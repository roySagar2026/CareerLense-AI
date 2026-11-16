import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Check, ChevronDown, FileSearch, Gauge, KeyRound, Layers, Lock, ShieldCheck, Target, Trash2, Upload, X } from "lucide-react";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/utils/cn";

const features = [
  { icon: FileSearch, title: "Structure-aware parsing", text: "PDF and DOCX resumes are split into summary, skills, experience, projects, education and more, with an extraction confidence." },
  { icon: Target, title: "Requirement extraction", text: "Job descriptions are broken into required and preferred skills, responsibilities, experience and education." },
  { icon: KeyRound, title: "Hybrid keyword matching", text: "Exact, alias-aware, fuzzy and related-skill matching. Related skills never count as proven experience." },
  { icon: Gauge, title: "Explainable score", text: "Six weighted dimensions with a visible formula. Repeated keywords can't inflate the score." },
  { icon: Layers, title: "Section-level analysis", text: "See which resume sections need work, what's strong, and where each missing keyword would fit." },
  { icon: ShieldCheck, title: "Honest recommendations", text: "Suggestions are labelled as suggestions. CareerLens never invents skills, projects or experience for you." },
];

const steps = [
  { n: "1", title: "Upload your resume", text: "Drag in a PDF or DOCX. Review and correct the extracted sections." },
  { n: "2", title: "Add a job description", text: "Paste the text or import a public job posting link." },
  { n: "3", title: "Review the analysis", text: "Matched and missing keywords, section feedback and prioritized actions." },
];

const faqs = [
  { q: "Is this the score an employer's ATS gives me?", a: "No. Employers use different, proprietary systems. CareerLens produces a transparent heuristic alignment score so you can see how your resume lines up with a specific job description. It is never an official ATS score." },
  { q: "Will it add skills to my resume?", a: "No. Recommendations tell you where a keyword could fit if you genuinely have that experience. Nothing is added automatically and nothing is invented." },
  { q: "Does it use a paid AI service?", a: "The core analysis runs without any paid LLM API. Parsing, keyword matching and scoring are deterministic and explainable." },
  { q: "What happens to my resume?", a: "It is stored privately, only visible to your account, and never exposed through a public link. You can delete any resume, analysis, or your whole account at any time." },
  { q: "Can I import a job posting link?", a: "Yes, for public pages. Some sites block automated access, in which case you can paste the text instead." },
];

function SampleCard() {
  const rows = [
    { k: "Python", s: "Matched", tone: "success" as const },
    { k: "PostgreSQL", s: "Matched", tone: "success" as const },
    { k: "Django", s: "Related skill (not verified)", tone: "warning" as const },
    { k: "Docker", s: "Missing, suggested: Projects", tone: "danger" as const },
  ];
  return (
    <Card className="w-full max-w-md p-5 text-left shadow-2xl">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-medium">Illustrative example</p>
        <Badge tone="neutral">Sample data</Badge>
      </div>
      <ul className="space-y-2.5">
        {rows.map((r) => (
          <li key={r.k} className="flex items-center justify-between gap-3 text-sm">
            <span className="font-medium">{r.k}</span>
            <Badge tone={r.tone}>
              {r.tone === "success" ? <Check className="h-3 w-3" /> : r.tone === "danger" ? <X className="h-3 w-3" /> : null}
              {r.s}
            </Badge>
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t pt-3 text-xs text-muted">
        A mock-up of the keyword view. Your real results come from your own resume and job description.
      </p>
    </Card>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const [open, setOpen] = useState<number | null>(0);
  const cta = user ? "/app/analyze" : "/register";

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <nav aria-label="Primary" className="hidden items-center gap-6 text-sm text-muted md:flex">
            <a href="#features" className="hover:text-foreground">Features</a>
            <a href="#how" className="hover:text-foreground">How it works</a>
            <a href="#privacy" className="hover:text-foreground">Privacy</a>
            <a href="#pricing" className="hover:text-foreground">Pricing</a>
            <a href="#faq" className="hover:text-foreground">FAQ</a>
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <Button asChild size="sm"><Link to="/app">Open dashboard</Link></Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm"><Link to="/login">Sign in</Link></Button>
                <Button asChild size="sm"><Link to="/register">Get started</Link></Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden"><div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-[28rem] bg-[radial-gradient(60%_60%_at_70%_0%,rgb(57_120_246/0.12),transparent)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <Badge tone="primary" className="mb-4">Resume intelligence, explained</Badge>
            <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
              See exactly how your resume lines up with the job.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-muted">
              CareerLens AI compares your resume to a job description and shows matched, related and missing keywords, section-by-section
              feedback, and a transparent alignment score.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg"><Link to={cta}>Analyze My Resume</Link></Button>
              <Button asChild variant="secondary" size="lg"><a href="#how">How it works</a></Button>
            </div>
            <p className="mt-4 text-xs text-muted">The score is a heuristic estimate for your own guidance, not an employer ATS score.</p>
          </motion.div>
          <motion.div className="flex justify-center lg:justify-end" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15, duration: 0.5 }}>
            <SampleCard />
          </motion.div>
        </div>
        </section>

        <section id="features" className="border-t bg-surface/50 py-16">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold">Built to be accurate, not flattering</h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, title, text }, i) => (
                <motion.div
                  key={title}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-40px" }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                >
                  <Card className="h-full p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-lift">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" aria-hidden />
                    </div>
                    <h3 className="mt-3 font-semibold">{title}</h3>
                    <p className="mt-1 text-sm text-muted">{text}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="how" className="py-16">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold">How it works</h2>
            <ol className="mt-8 grid gap-4 md:grid-cols-3">
              {steps.map((s) => (
                <li key={s.n} className="rounded-xl border bg-card p-5 shadow-card">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">{s.n}</span>
                  <h3 className="mt-3 font-semibold">{s.title}</h3>
                  <p className="mt-1 text-sm text-muted">{s.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="privacy" className="border-t bg-surface/50 py-16">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 sm:px-6 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-semibold">Your resume is sensitive. We treat it that way.</h2>
              <p className="mt-2 text-muted">Resumes contain personal details, so privacy controls are part of the product, not an afterthought.</p>
            </div>
            <ul className="space-y-3 text-sm">
              {[
                [Lock, "Private storage. Files are never exposed through public URLs."],
                [ShieldCheck, "Argon2 password hashing, rotating refresh tokens, per-user data isolation."],
                [Upload, "Strict file validation: type, size and content checks on every upload."],
                [Trash2, "Delete any resume or analysis, or your entire account, whenever you like."],
              ].map(([Icon, text], i) => {
                const I = Icon as typeof Lock;
                return (
                  <li key={i} className="flex gap-3">
                    <I className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                    <span>{text as string}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>

        <section id="pricing" className="py-16">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
            <h2 className="text-2xl font-semibold">Pricing</h2>
            <Card className="mt-6 p-6">
              <Badge tone="success">Free</Badge>
              <p className="mt-3 text-sm text-muted">
                CareerLens AI is free to use. Plans and billing are not implemented yet; the account model is ready for them.
              </p>
              <Button asChild className="mt-5"><Link to={cta}>Analyze My Resume</Link></Button>
            </Card>
          </div>
        </section>

        <section id="faq" className="border-t bg-surface/50 py-16">
          <div className="mx-auto max-w-3xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold">Frequently asked questions</h2>
            <div className="mt-6 divide-y rounded-xl border bg-card shadow-card">
              {faqs.map((f, i) => (
                <div key={f.q}>
                  <h3>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between gap-4 px-4 py-4 text-left text-sm font-medium"
                      aria-expanded={open === i}
                      aria-controls={`faq-${i}`}
                      onClick={() => setOpen(open === i ? null : i)}
                    >
                      {f.q}
                      <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted transition-transform", open === i && "rotate-180")} aria-hidden />
                    </button>
                  </h3>
                  {open === i && (
                    <p id={`faq-${i}`} className="px-4 pb-4 text-sm text-muted">
                      {f.a}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm text-muted sm:flex-row sm:px-6">
          <Logo />
          <p>CareerLens AI provides heuristic guidance. It is not affiliated with any employer or ATS vendor.</p>
        </div>
      </footer>
    </div>
  );
}
