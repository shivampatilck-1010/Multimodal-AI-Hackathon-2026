import { Bot, FileCheck2, TrendingUp, FolderGit2, Network, Settings, ArrowLeft } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  memberOwner: string;
  onBackToDashboard: () => void;
}

const BasePlaceholder: React.FC<PlaceholderPageProps> = ({
  title,
  description,
  icon,
  memberOwner,
  onBackToDashboard,
}) => {
  return (
    <div className="card-surface" style={{ padding: "48px 32px", textAlign: "center", maxWidth: "640px", margin: "40px auto" }}>
      <div
        style={{
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          backgroundColor: "var(--primary-50)",
          color: "var(--primary-600)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 16px",
        }}
      >
        {icon}
      </div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "8px" }}>{title}</h1>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", lineHeight: 1.6, marginBottom: "16px" }}>
        {description}
      </p>
      <div
        style={{
          display: "inline-block",
          fontSize: "0.75rem",
          fontWeight: 600,
          color: "var(--primary-700)",
          background: "var(--primary-50)",
          padding: "4px 12px",
          borderRadius: "var(--border-radius-full)",
          marginBottom: "24px",
        }}
      >
        Owned by {memberOwner} • Frontend integration ready
      </div>
      <div>
        <button className="btn-primary" onClick={onBackToDashboard}>
          <ArrowLeft size={16} />
          <span>Back to Student Dashboard</span>
        </button>
      </div>
    </div>
  );
};

export const TutorPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="AI Tutor & Conversational RAG"
    description="Interactive conversational tutoring layer with strict evidence-gating and verified citation validation."
    icon={<Bot size={28} />}
    memberOwner="Member 2 (RAG & AI Tutor)"
    onBackToDashboard={onBack}
  />
);

export const AssessmentsPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="Adaptive Assessments & Mock Exams"
    description="Grounded MCQ and problem-solving generation based directly on textbook excerpts and slide concepts."
    icon={<FileCheck2 size={28} />}
    memberOwner="Member 3 (Assessment Engineer)"
    onBackToDashboard={onBack}
  />
);

export const ProgressPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="Student Mastery & Longitudinal Progress"
    description="Bayesian Knowledge Tracing and IRT mastery tracking across all course topics and subtopics."
    icon={<TrendingUp size={28} />}
    memberOwner="Member 4 (Learner Model)"
    onBackToDashboard={onBack}
  />
);

export const MaterialsPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="Multimodal Course Materials"
    description="Extracted textbooks, lecture slides, video transcripts, and diagrams with exact source location links."
    icon={<FolderGit2 size={28} />}
    memberOwner="Member 1 (Multimodal Knowledge Base)"
    onBackToDashboard={onBack}
  />
);

export const CourseMapPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="Curriculum Prerequisite Knowledge Graph"
    description="Interactive visual directed acyclic graph (DAG) mapping topic dependencies and optimal learning pathways."
    icon={<Network size={28} />}
    memberOwner="Member 1 (Knowledge Graph Engine)"
    onBackToDashboard={onBack}
  />
);

export const SettingsPage: React.FC<{ onBack: () => void }> = ({ onBack }) => (
  <BasePlaceholder
    title="Student Settings & Preferences"
    description="Configure tutoring difficulty levels (Beginner, Intermediate, Advanced), notification pacing, and course scope."
    icon={<Settings size={28} />}
    memberOwner="Platform Settings"
    onBackToDashboard={onBack}
  />
);
