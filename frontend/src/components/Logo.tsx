import { Link } from "react-router-dom";

export function LogoMark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect width="32" height="32" rx="8" fill="#3978F6" />
      <circle cx="15" cy="15" r="7" fill="none" stroke="#FFFFFF" strokeWidth="2.5" />
      <path d="M20.5 20.5 26 26" stroke="#253247" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="flex items-center gap-2 font-heading font-semibold tracking-tight">
      <LogoMark />
      <span>
        CareerLens <span className="text-primary">AI</span>
      </span>
    </Link>
  );
}
