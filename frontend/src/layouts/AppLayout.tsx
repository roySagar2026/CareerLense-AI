import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { BarChart3, Briefcase, FileText, History, LayoutDashboard, LogOut, Menu, Settings, Sparkles, X } from "lucide-react";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/utils/cn";

const nav = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/resumes", label: "Resumes", icon: FileText },
  { to: "/app/jobs", label: "Job descriptions", icon: Briefcase },
  { to: "/app/analyze", label: "New analysis", icon: Sparkles },
  { to: "/app/history", label: "History", icon: History },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const signOut = async () => {
    await logout().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  const sidebar = (
    <nav aria-label="Main" className="flex h-full flex-col">
      <div className="flex h-16 items-center px-5">
        <Logo to="/app" />
      </div>
      <ul className="flex-1 space-y-1 px-3 py-2">
        {nav.map(({ to, label, icon: Icon, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200",
                  isActive ? "bg-primary/10 text-primary" : "text-ink/70 hover:bg-surface hover:text-ink",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute inset-y-1.5 left-0 w-1 rounded-full bg-primary"
                      transition={{ duration: 0.25 }}
                    />
                  )}
                  <Icon className="h-4 w-4" aria-hidden />
                  {label}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="border-t p-3">
        <div className="mb-2 flex items-center gap-2 px-2">
          <BarChart3 className="h-4 w-4 text-accent" aria-hidden />
          <p className="text-xs text-muted">Scores are heuristic estimates, not employer ATS scores.</p>
        </div>
        <div className="flex items-center justify-between gap-2 px-2 py-1">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{user?.full_name || "Account"}</p>
            <p className="truncate text-xs text-muted">{user?.email}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sign out">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </nav>
  );

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-card lg:block">{sidebar}</aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink/40" onClick={() => setOpen(false)} aria-hidden />
          <aside className="relative h-full w-72 max-w-[85%] animate-fade-in border-r bg-card shadow-lift">
            <Button variant="ghost" size="icon" className="absolute right-2 top-3" onClick={() => setOpen(false)} aria-label="Close menu">
              <X className="h-4 w-4" />
            </Button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-card/90 px-4 backdrop-blur lg:hidden">
          <Button variant="ghost" size="icon" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
          <Logo to="/app" />
        </header>
        <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
}
