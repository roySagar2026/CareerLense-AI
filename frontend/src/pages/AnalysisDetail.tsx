import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { GitCompare, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/States";
import { PageSkeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { ScoreOverview } from "@/components/analysis/ScoreOverview";
import { KeywordExplorer } from "@/components/analysis/KeywordExplorer";
import { SkillsComparison } from "@/components/analysis/SkillsComparison";
import { SectionAnalysisView } from "@/components/analysis/SectionAnalysisView";
import { RecommendationList } from "@/components/analysis/RecommendationList";
import { PlacementSuggestions } from "@/components/analysis/PlacementSuggestions";
import { useAnalysis, useDeleteMutation } from "@/hooks/useQueries";
import { useToast } from "@/contexts/ToastContext";
import { analysisApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import { formatDateTime } from "@/utils/format";

export default function AnalysisDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { data: a, isLoading, isError, error, refetch } = useAnalysis(id);
  const [confirm, setConfirm] = useState(false);
  const remove = useDeleteMutation(analysisApi.remove, () => {
    toast.success("Analysis deleted.");
    navigate("/app/history", { replace: true });
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !a) return <ErrorState error={error} onRetry={() => refetch()} />;

  return (
    <div>
      <PageHeader
        title={`${a.job_title}${a.company ? ` · ${a.company}` : ""}`}
        description={`${a.resume_name} (v${a.resume_version}) · analyzed ${formatDateTime(a.created_at)}`}
        actions={
          <>
            <Button asChild variant="secondary"><Link to={`/app/compare?a=${a.id}`}><GitCompare className="h-4 w-4" />Compare</Link></Button>
            <Button asChild variant="secondary"><Link to={`/app/resumes/${a.resume_id}`}>View resume</Link></Button>
            <Button variant="ghost" aria-label="Delete analysis" onClick={() => setConfirm(true)}><Trash2 className="h-4 w-4" /></Button>
          </>
        }
      />
      <Tabs defaultValue="overview">
        <TabsList aria-label="Analysis sections">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="keywords">Keywords</TabsTrigger>
          <TabsTrigger value="skills">Skills comparison</TabsTrigger>
          <TabsTrigger value="sections">Resume sections</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="placement">Keyword placement</TabsTrigger>
        </TabsList>
        <TabsContent value="overview"><ScoreOverview analysis={a} /></TabsContent>
        <TabsContent value="keywords"><KeywordExplorer analysis={a} /></TabsContent>
        <TabsContent value="skills"><SkillsComparison analysis={a} /></TabsContent>
        <TabsContent value="sections"><SectionAnalysisView analysis={a} /></TabsContent>
        <TabsContent value="recommendations"><RecommendationList analysisId={a.id} /></TabsContent>
        <TabsContent value="placement"><PlacementSuggestions analysisId={a.id} /></TabsContent>
      </Tabs>
      <ConfirmDialog open={confirm} onOpenChange={setConfirm} title="Delete this analysis?" description="This permanently deletes the analysis results. Your resume and job description are kept." confirmLabel="Delete analysis" loading={remove.isPending} onConfirm={() => remove.mutate(id, { onError: (e) => toast.error(errorMessage(e)) })} />
    </div>
  );
}
