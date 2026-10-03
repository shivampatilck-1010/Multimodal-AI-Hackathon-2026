import { CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";
import type { AssessmentSummary } from "../types/dashboard";

interface RecentAssessmentProps {
  assessment: AssessmentSummary;
  onViewReport: (assessmentId: string) => void;
}

export const RecentAssessment: React.FC<RecentAssessmentProps> = ({
  assessment,
  onViewReport,
}) => {
  return (
    <section className="card-surface" aria-labelledby="assessment-card-title">
      <div className="card-title-row">
        <h2 id="assessment-card-title" className="card-heading">
          Latest Assessment
        </h2>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {assessment.completedAt}
        </span>
      </div>

      <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-secondary)" }}>
        {assessment.topicName}
      </div>

      <div className="assessment-score-row">
        <span className="assessment-score-large">
          {assessment.score} <span style={{ fontSize: "1.25rem", color: "var(--text-muted)", fontWeight: 500 }}>/ {assessment.totalQuestions}</span>
        </span>
        <div className="assessment-score-breakdown">
          <span className="score-correct">✓ {assessment.correctCount} Correct</span>
          <span className="score-incorrect">✕ {assessment.incorrectCount} Incorrect</span>
        </div>
      </div>

      <div className="concept-tags-list">
        <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)" }}>
          Strengths
        </span>
        {assessment.strongAreas.map((area, idx) => (
          <div key={idx} className="concept-tag-strong">
            <CheckCircle2 size={15} style={{ flexShrink: 0 }} />
            <span>{area}</span>
          </div>
        ))}

        <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)", marginTop: "8px" }}>
          Needs Work
        </span>
        {assessment.weakAreas.map((area, idx) => (
          <div key={idx} className="concept-tag-weak">
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            <span>{area}</span>
          </div>
        ))}
      </div>

      <button
        className="btn-secondary"
        style={{ width: "100%", justifyContent: "center", marginTop: "12px" }}
        onClick={() => onViewReport(assessment.id)}
      >
        <span>View Report</span>
        <ArrowRight size={15} />
      </button>
    </section>
  );
};
