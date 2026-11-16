import { Badge } from "@/components/ui/Badge";
import { formatScore, scoreTone } from "@/utils/format";

export function ScoreBadge({ score }: { score: number | null }) {
  const tone = scoreTone(score);
  return <Badge tone={tone === "muted" ? "neutral" : tone}>{formatScore(score)}/100</Badge>;
}
