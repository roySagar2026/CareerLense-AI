import { cn } from "@/utils/cn";
import { formatScore, scoreTone } from "@/utils/format";

const strokes = {
  success: "stroke-success",
  warning: "stroke-warning",
  danger: "stroke-danger",
  muted: "stroke-muted",
} as const;

export function ScoreRing({ score, size = 140, label = "Alignment score" }: { score: number | null; size?: number; label?: string }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const value = score === null ? 0 : Math.max(0, Math.min(100, score));
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 120 120" className="-rotate-90" width={size} height={size} role="img" aria-label={`${label}: ${formatScore(score)} out of 100`}>
        <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10" className="stroke-border" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - value / 100)}
          className={cn("transition-[stroke-dashoffset] duration-700", strokes[scoreTone(score)])}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums">{formatScore(score)}</span>
        <span className="text-xs text-muted">out of 100</span>
      </div>
    </div>
  );
}

export function ScoreBar({ score, className }: { score: number | null; className?: string }) {
  const tone = scoreTone(score);
  const bg = { success: "bg-success", warning: "bg-warning", danger: "bg-danger", muted: "bg-muted" }[tone];
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-border", className)}>
      <div className={cn("h-full rounded-full transition-all duration-500", bg)} style={{ width: `${score ?? 0}%` }} />
    </div>
  );
}
