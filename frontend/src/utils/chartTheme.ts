// Chart colours mirror the CSS design tokens in styles/globals.css (Recharts needs literal values).
export const chartColors = {
  primary: "#3978F6",
  grid: "#E2E8F0",
  axis: "#64748B",
  success: "#15803D",
  warning: "#B45309",
  danger: "#DC2626",
  muted: "#94A3B8",
} as const;

export const tooltipStyle = {
  background: "#FFFFFF",
  border: "1px solid #E2E8F0",
  borderRadius: 12,
  boxShadow: "0 8px 24px -6px rgba(23,32,51,0.12)",
  color: "#172033",
} as const;
