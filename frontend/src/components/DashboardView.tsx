import { useState } from "react";
import type { DashboardData, DashboardViewMode, TopicData } from "../types/dashboard";
import { SummaryCards } from "./SummaryCards";
import { TopicMastery } from "./TopicMastery";
import { PriorityTopic } from "./PriorityTopic";
import { RecommendationCard } from "./RecommendationCard";
import { RecentAssessment } from "./RecentAssessment";
import { ContinueLearning } from "./ContinueLearning";
import { TutorQuickAction } from "./TutorQuickAction";
import { LearningActivity } from "./LearningActivity";
import { MasteryTrend } from "./MasteryTrend";
import { CourseMaterials } from "./CourseMaterials";
import { TopicDetailModal } from "./TopicDetailModal";
import { SkeletonLoader } from "./SkeletonLoader";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { NewStudentState } from "./NewStudentState";

interface DashboardViewProps {
  data: DashboardData;
  viewMode: DashboardViewMode;
  onNavigateToRoute: (route: any) => void;
  onRetry: () => void;
  onStartDiagnostic: () => void;
  onShowToast: (message: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  data,
  viewMode,
  onNavigateToRoute,
  onRetry,
  onStartDiagnostic,
  onShowToast,
}) => {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);

  // 1. Loading State
  if (viewMode === "loading") {
    return <SkeletonLoader />;
  }

  // 2. Error State
  if (viewMode === "error") {
    return <ErrorState onRetry={onRetry} />;
  }

  // 3. New Student State
  if (viewMode === "new_student") {
    return (
      <NewStudentState
        studentName={data.student.name}
        onStartDiagnostic={onStartDiagnostic}
      />
    );
  }

  // 4. Empty State
  if (viewMode === "empty") {
    return (
      <EmptyState
        title="No course materials or progress yet"
        message="This course is newly initialized. Ask the instructor or upload course materials to begin learning."
        actionLabel="View Course Materials"
        onAction={() => onNavigateToRoute("materials")}
      />
    );
  }

  // 5. Standard Dashboard View
  return (
    <>
      {/* Greeting Banner */}
      <header className="dashboard-header">
        <h1 className="dashboard-title">Good morning, {data.student.name.split(" ")[0]} 👋</h1>
        <p className="dashboard-subtitle">
          Here's where you should focus today for <strong>{data.course.name} ({data.course.code})</strong>.
        </p>
      </header>

      {/* Summary KPI Metrics */}
      <SummaryCards metrics={data.summary} />

      {/* Two-Column Responsive Workspace */}
      <div className="dashboard-main-grid">
        {/* Left Column: Topics, Activity, and Mastery Trends */}
        <div className="dashboard-left-col">
          <TopicMastery
            topics={data.topics}
            onSelectTopic={(topic) => setSelectedTopic(topic)}
          />

          <LearningActivity activity={data.activity} />

          <MasteryTrend history={data.masteryHistory} />
        </div>

        {/* Right Column: Priority Actions, Recommendations, and Assessments */}
        <div className="dashboard-right-col">
          <PriorityTopic
            priority={data.priorityTopic}
            onReview={(tName) => {
              const matched = data.topics.find((t) => t.name === tName);
              if (matched) setSelectedTopic(matched);
              else onShowToast(`Opening review materials for ${tName}...`);
            }}
            onPractice={(tName) => {
              onShowToast(`Launching targeted practice quiz for ${tName}...`);
            }}
          />

          <RecommendationCard
            recommendation={data.recommendation}
            onAction={(actionName) => onShowToast(`Initiated: ${actionName}`)}
          />

          <RecentAssessment
            assessment={data.assessment}
            onViewReport={(id) => onShowToast(`Opening assessment report #${id}...`)}
          />

          <ContinueLearning
            data={data.continueLearning}
            onContinue={() => onShowToast(`Resuming session on ${data.continueLearning.currentTopic}...`)}
          />

          <TutorQuickAction
            onAskTutor={(prompt) => {
              onNavigateToRoute("tutor");
              if (prompt) onShowToast(`Sent prompt to AI Tutor: "${prompt}"`);
            }}
          />

          <CourseMaterials
            materials={data.materials}
            onViewMaterials={() => onNavigateToRoute("materials")}
          />
        </div>
      </div>

      {/* Interactive Topic Modal */}
      {selectedTopic && (
        <TopicDetailModal
          topic={selectedTopic}
          onClose={() => setSelectedTopic(null)}
          onActionClick={(actionName) => {
            onShowToast(actionName);
            setSelectedTopic(null);
          }}
        />
      )}
    </>
  );
};
