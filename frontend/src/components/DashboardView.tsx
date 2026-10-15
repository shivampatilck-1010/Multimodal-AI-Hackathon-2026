
import { useState } from "react";
import {
  getConceptEvidence,
  getCourseConcepts,
} from "../client";
import type { ConceptEvidence } from "../client";
import type {
  DashboardData,
  DashboardViewMode,
  TopicData,
} from "../types/dashboard";

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

function normalize(value: string): string {
  return value
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
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
  const [evidence, setEvidence] = useState<ConceptEvidence | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  function openTopic(topic: TopicData) {
    setSelectedTopic(topic);
    setEvidence(null);
    setEvidenceError(null);
    setEvidenceLoading(false);
  }

  function closeTopic() {
    setSelectedTopic(null);
    setEvidence(null);
    setEvidenceError(null);
    setEvidenceLoading(false);
  }

  async function handleTopicAction(actionName: string): Promise<void> {
    const topic = selectedTopic;

    if (!topic) return;

    if (actionName.startsWith("Review Material for ")) {
      setEvidence(null);
      setEvidenceError(null);
      setEvidenceLoading(true);

      try {
        const concepts = await getCourseConcepts(data.course.id);
        const target = normalize(topic.name);

        const exactMatches = concepts.filter(
          (concept) =>
            normalize(concept.topic) === target ||
            normalize(concept.name) === target,
        );

        const partialMatches =
          exactMatches.length > 0
            ? exactMatches
            : concepts.filter((concept) => {
                const name = normalize(concept.name);
                const conceptTopic = normalize(concept.topic);

                return (
                  name.includes(target) ||
                  target.includes(name) ||
                  conceptTopic.includes(target) ||
                  target.includes(conceptTopic)
                );
              });

        if (partialMatches.length !== 1) {
          throw new Error(
            partialMatches.length === 0
              ? `No backend concept matches "${topic.name}".`
              : `More than one backend concept matches "${topic.name}".`,
          );
        }

        const result = await getConceptEvidence(
          data.course.id,
          partialMatches[0].id,
        );

        setEvidence(result);

        if (result.units.length === 0 && result.figures.length === 0) {
          setEvidenceError(
            "This concept has no linked course evidence yet.",
          );
        }
      } catch (error) {
        console.error("Failed to retrieve course evidence:", error);
        setEvidenceError(
          error instanceof Error
            ? error.message
            : "Unable to retrieve course evidence.",
        );
      } finally {
        setEvidenceLoading(false);
      }

      return;
    }

    if (actionName.startsWith("Ask Tutor about ")) {
      onNavigateToRoute("tutor");
      onShowToast(`Opening the AI Tutor for ${topic.name}.`);
      return;
    }

    if (actionName.startsWith("Practice Questions on ")) {
      onShowToast(`Launching practice questions for ${topic.name}.`);
      return;
    }

    onShowToast(actionName);
  }

  if (viewMode === "loading") {
    return <SkeletonLoader />;
  }

  if (viewMode === "error") {
    return <ErrorState onRetry={onRetry} />;
  }

  if (viewMode === "new_student") {
    return (
      <NewStudentState
        studentName={data.student.name}
        onStartDiagnostic={onStartDiagnostic}
      />
    );
  }

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

  return (
    <>
      <header className="dashboard-header">
        <h1 className="dashboard-title">
          Good morning, {data.student.name.split(" ")[0]}
        </h1>
        <p className="dashboard-subtitle">
          Here's where you should focus today for{" "}
          <strong>
            {data.course.name} ({data.course.code})
          </strong>
          .
        </p>
      </header>

      <SummaryCards metrics={data.summary} />

      <div className="dashboard-main-grid">
        <div className="dashboard-left-col">
          <TopicMastery topics={data.topics} onSelectTopic={openTopic} />
          <LearningActivity activity={data.activity} />
          <MasteryTrend history={data.masteryHistory} />
        </div>

        <div className="dashboard-right-col">
          <PriorityTopic
            priority={data.priorityTopic}
            onReview={(topicName) => {
              const matched = data.topics.find(
                (topic) => topic.name === topicName,
              );

              if (matched) {
                openTopic(matched);
              } else {
                onShowToast(`No dashboard topic was found for ${topicName}.`);
              }
            }}
            onPractice={(topicName) =>
              onShowToast(`Launching practice questions for ${topicName}.`)
            }
          />

          <RecommendationCard
            recommendation={data.recommendation}
            onAction={(actionName) =>
              onShowToast(`Initiated: ${actionName}`)
            }
          />

          <RecentAssessment
            assessment={data.assessment}
            onViewReport={(id) =>
              onShowToast(`Opening assessment report #${id}.`)
            }
          />

          <ContinueLearning
            data={data.continueLearning}
            onContinue={() =>
              onShowToast(
                `Resuming session on ${data.continueLearning.currentTopic}.`,
              )
            }
          />

          <TutorQuickAction
            onAskTutor={(prompt) => {
              onNavigateToRoute("tutor");

              if (prompt) {
                onShowToast("Opening the AI Tutor with your question.");
              }
            }}
          />

          <CourseMaterials
            materials={data.materials}
            onViewMaterials={() => onNavigateToRoute("materials")}
          />
        </div>
      </div>

      {selectedTopic && (
        <TopicDetailModal
          topic={selectedTopic}
          evidence={evidence}
          evidenceLoading={evidenceLoading}
          evidenceError={evidenceError}
          onClose={closeTopic}
          onActionClick={handleTopicAction}
        />
      )}
    </>
  );
};
