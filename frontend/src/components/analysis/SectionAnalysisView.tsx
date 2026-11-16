import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { AnalysisDetail } from "@/types/api";
import { titleCase } from "@/utils/format";
import { PRIORITY_TONE } from "./labels";

function List({ title, items, empty }: { title: string; items: string[]; empty?: string }) {
  return (
    <div>
      <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">{title}</h4>
      {items.length === 0 ? <p className="text-sm text-muted">{empty ?? "None"}</p> : <ul className="list-inside list-disc space-y-0.5 text-sm">{items.map((i) => <li key={i}>{i}</li>)}</ul>}
    </div>
  );
}

export function SectionAnalysisView({ analysis }: { analysis: AnalysisDetail }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {analysis.section_analysis.map((s) => (
        <Card key={s.section_type}>
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h3 className="font-medium">{titleCase(s.section_type)}</h3>
            <div className="flex gap-2">
              {!s.present && <Badge tone="danger">Not found</Badge>}
              <Badge tone={PRIORITY_TONE[s.priority]}>{s.priority} priority</Badge>
            </div>
          </div>
          <CardBody className="space-y-4">
            <List title="Strengths" items={s.strengths} empty="Nothing notable yet" />
            <List title="Missing information" items={s.missing} />
            {s.relevant_keywords.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">Relevant keywords here</h4>
                <div className="flex flex-wrap gap-1">{s.relevant_keywords.map((k) => <Badge key={k} tone="primary">{k}</Badge>)}</div>
              </div>
            )}
            <List title="Recommendations" items={s.recommendations} />
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
