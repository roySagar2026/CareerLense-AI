import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { GuestRoute, ProtectedRoute } from "@/components/ProtectedRoute";
import { AppLayout } from "@/layouts/AppLayout";
import { PageSkeleton } from "@/components/ui/Skeleton";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import NotFound from "@/pages/NotFound";

// Heavy pages (charts) are split out of the entry bundle.
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Resumes = lazy(() => import("@/pages/Resumes"));
const ResumeDetail = lazy(() => import("@/pages/ResumeDetail"));
const Jobs = lazy(() => import("@/pages/Jobs"));
const JobDetail = lazy(() => import("@/pages/JobDetail"));
const NewAnalysis = lazy(() => import("@/pages/NewAnalysis"));
const AnalysisDetail = lazy(() => import("@/pages/AnalysisDetail"));
const History = lazy(() => import("@/pages/History"));
const Compare = lazy(() => import("@/pages/Compare"));
const Settings = lazy(() => import("@/pages/Settings"));

export default function App() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-5xl p-8"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/app" element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="resumes" element={<Resumes />} />
            <Route path="resumes/:id" element={<ResumeDetail />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/:id" element={<JobDetail />} />
            <Route path="analyze" element={<NewAnalysis />} />
            <Route path="analysis/:id" element={<AnalysisDetail />} />
            <Route path="history" element={<History />} />
            <Route path="compare" element={<Compare />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
