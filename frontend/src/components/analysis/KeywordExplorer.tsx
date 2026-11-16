import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Field";
import { ErrorState } from "@/components/ui/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { useKeywords } from "@/hooks/useQueries";
import type { AnalysisDetail, ResultCategory } from "@/types/api";
import { titleCase } from "@/utils/format";
import { CATEGORY_META, IMPORTANCE_TONE, MATCH_TYPE_LABEL } from "./labels";

const PAGE_SIZE = 15;

export function KeywordExplorer({ analysis }: { analysis: AnalysisDetail }) {
  const [category, setCategory] = useState<string>("");
  const [importance, setImportance] = useState("");
  const [kind, setKind] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const t = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 250);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  const { data, isLoading, isError, error, refetch, isFetching } = useKeywords(analysis.id, {
    result_category: category, importance, kind, search, page, page_size: PAGE_SIZE,
  });
  const counts = analysis.keyword_counts;
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by match category">
        <Button size="sm" variant={category === "" ? "primary" : "secondary"} onClick={() => { setCategory(""); setPage(1); }}>All</Button>
        {(Object.keys(CATEGORY_META) as ResultCategory[]).map((c) => (
          <Button key={c} size="sm" variant={category === c ? "primary" : "secondary"} aria-pressed={category === c} onClick={() => { setCategory(c); setPage(1); }}>
            {CATEGORY_META[c].label} <span className="tabular-nums opacity-80">{counts[c]}</span>
          </Button>
        ))}
      </div>
      {category && <p className="text-sm text-muted">{CATEGORY_META[category as ResultCategory].help}</p>}

      <div className="flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
          <Input className="pl-9" placeholder="Search keywords" aria-label="Search keywords" value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
        </div>
        <Select aria-label="Filter by importance" className="w-auto" value={importance} onChange={(e) => { setImportance(e.target.value); setPage(1); }}>
          <option value="">Any importance</option><option value="required">Required</option><option value="preferred">Preferred</option><option value="contextual">Contextual</option>
        </Select>
        <Select aria-label="Filter by type" className="w-auto" value={kind} onChange={(e) => { setKind(e.target.value); setPage(1); }}>
          <option value="">Any type</option><option value="skill">Skills</option><option value="responsibility">Responsibilities</option><option value="experience">Experience</option><option value="education">Education</option><option value="certification">Certifications</option>
        </Select>
      </div>

      {isLoading ? (
        <Skeleton className="h-64" />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : data && data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted">No keywords match these filters.</p>
      ) : (
        <Card className={isFetching ? "opacity-70 transition-opacity" : undefined}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-sm">
              <thead className="border-b text-left text-xs text-muted">
                <tr><th className="px-4 py-2">Keyword</th><th className="px-3 py-2">Result</th><th className="px-3 py-2">Importance</th><th className="px-3 py-2">Category</th><th className="px-3 py-2 text-right">In resume</th><th className="px-3 py-2">Suggested section</th><th className="px-4 py-2">Why</th></tr>
              </thead>
              <tbody className="divide-y align-top">
                {data?.items.map((k) => {
                  const meta = CATEGORY_META[k.result_category];
                  return (
                    <tr key={k.id}>
                      <td className="px-4 py-2.5">
                        <p className="font-medium">{k.normalized_keyword}</p>
                        {k.original_keyword.toLowerCase() !== k.normalized_keyword.toLowerCase() && <p className="text-xs text-muted">as written: {k.original_keyword}</p>}
                      </td>
                      <td className="px-3 py-2.5"><Badge tone={meta.tone}>{meta.label}</Badge><p className="mt-1 text-xs text-muted">{MATCH_TYPE_LABEL[k.match_type]} · {Math.round(k.confidence * 100)}% confidence</p></td>
                      <td className="px-3 py-2.5"><Badge tone={IMPORTANCE_TONE[k.importance]}>{k.importance}</Badge></td>
                      <td className="px-3 py-2.5 text-muted">{titleCase(k.category || k.kind)}</td>
                      <td className="px-3 py-2.5 text-right tabular-nums">{k.occurrences}</td>
                      <td className="px-3 py-2.5 text-muted">{k.suggested_section ? titleCase(k.suggested_section) : "—"}</td>
                      <td className="max-w-xs px-4 py-2.5 text-xs text-muted">{k.explanation}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-muted">
            <span>{data?.total ?? 0} keywords</span>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Previous page"><ChevronLeft className="h-4 w-4" /></Button>
              <span>Page {page} of {pages}</span>
              <Button variant="ghost" size="icon" disabled={page >= pages} onClick={() => setPage(page + 1)} aria-label="Next page"><ChevronRight className="h-4 w-4" /></Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
