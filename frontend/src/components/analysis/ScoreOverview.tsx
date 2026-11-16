import { chartColors, tooltipStyle } from "@/utils/chartTheme";
import { Info } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScoreBar, ScoreRing } from "@/components/ui/ScoreRing";
import type { AnalysisDetail, DimensionKey } from "@/types/api";
import { formatScore, scoreTone } from "@/utils/format";

const ORDER: DimensionKey[] = ["required_skills", "preferred_skills", "experience", "responsibilities", "education", "structure"];
const COLOR = chartColors;

function Metric({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-md border bg-surface p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums">{formatScore(value)}</p>
      <ScoreBar score={value} className="mt-2 h-1.5" />
    </div>
  );
}

export function ScoreOverview({ analysis }: { analysis: AnalysisDetail }) {
  const m = analysis.metrics;
  const chart = ORDER.map((k) => ({ key: k, name: analysis.dimension_scores[k].label, score: analysis.dimension_scores[k].score ?? 0, na: analysis.dimension_scores[k].score === null }));

  return (
    <div className="space-y-6">
      <div role="note" className="flex gap-3 rounded-lg border border-accent/30 bg-accent/5 p-4 text-sm">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden />
        <p>{analysis.disclaimer}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="flex flex-col items-center justify-center p-6">
          <ScoreRing score={analysis.overall_score} size={168} label="Overall alignment score" />
          <p className="mt-3 text-sm font-medium">Overall alignment</p>
          <p className="text-xs text-muted">Heuristic estimate, engine v{analysis.engine_version}</p>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Headline metrics" />
          <CardBody className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Metric label="Skills alignment" value={m.skills_alignment} />
            <Metric label="Experience alignment" value={m.experience_alignment} />
            <Metric label="Education alignment" value={m.education_alignment} />
            <Metric label="Keyword coverage" value={m.keyword_coverage} />
            <Metric label="Structural quality" value={m.structural_quality} />
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Score breakdown" description="Each dimension (0–100) and how much it adds to the overall score." />
          <CardBody>
            <div className="h-60" role="img" aria-label="Bar chart of dimension scores">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chart} layout="vertical" margin={{ left: 10, right: 16 }}>
                  <XAxis type="number" domain={[0, 100]} stroke={chartColors.axis} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={130} stroke={chartColors.axis} tick={{ fontSize: 12 }} />
                  <Tooltip cursor={{ fill: "rgba(57,120,246,0.06)" }} contentStyle={tooltipStyle} formatter={(v: number, _n, item) => [item.payload.na ? "Not applicable" : `${Math.round(v)}/100`, "Score"]} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {chart.map((c) => <Cell key={c.key} fill={COLOR[c.na ? "muted" : scoreTone(c.score)]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="How the score is calculated" description="Transparent and configurable weights." />
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-sm">
              <thead className="border-b text-left text-xs text-muted"><tr><th className="px-4 py-2">Dimension</th><th className="px-2 py-2 text-right">Score</th><th className="px-2 py-2 text-right">Weight</th><th className="px-4 py-2 text-right">Adds</th></tr></thead>
              <tbody className="divide-y">
                {ORDER.map((k) => {
                  const d = analysis.dimension_scores[k];
                  return (
                    <tr key={k} title={d.explanation}>
                      <td className="px-4 py-2">{d.label}</td>
                      <td className="px-2 py-2 text-right tabular-nums">{d.score === null ? "n/a" : Math.round(d.score)}</td>
                      <td className="px-2 py-2 text-right tabular-nums">{d.effective_weight === null ? "—" : `${d.effective_weight.toFixed(0)}%`}</td>
                      <td className="px-4 py-2 text-right tabular-nums">+{d.contribution.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="border-t p-4 text-xs text-muted">
            <p>{analysis.scoring_config.formula}</p>
            <ul className="mt-2 space-y-1">
              {ORDER.map((k) => <li key={k}><span className="font-medium text-foreground/80">{analysis.dimension_scores[k].label}:</span> {analysis.dimension_scores[k].explanation}</li>)}
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}
