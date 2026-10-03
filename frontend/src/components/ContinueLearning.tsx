import { PlayCircle, ArrowRight } from "lucide-react";
import type { ContinueLearningData } from "../types/dashboard";

interface ContinueLearningProps {
  data: ContinueLearningData;
  onContinue: () => void;
}

export const ContinueLearning: React.FC<ContinueLearningProps> = ({
  data,
  onContinue,
}) => {
  return (
    <section className="card-surface" aria-labelledby="continue-learning-title">
      <div className="card-title-row">
        <h2 id="continue-learning-title" className="card-heading">
          Continue Learning
        </h2>
        <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary-600)" }}>
          IN PROGRESS
        </span>
      </div>

      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
        {data.courseName}
      </div>

      <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
        Current topic: <strong style={{ color: "var(--text-primary)" }}>{data.currentTopic}</strong>
      </div>

      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "16px" }}>
        Last activity: {data.lastActivity}
      </div>

      <div className="progress-track" style={{ marginBottom: "16px" }}>
        <div
          className="progress-fill fill-developing"
          style={{ width: `${data.progressPercentage}%` }}
        />
      </div>

      <button className="btn-primary" style={{ width: "100%", justifyContent: "center" }} onClick={onContinue}>
        <PlayCircle size={16} />
        <span>Continue</span>
        <ArrowRight size={15} />
      </button>
    </section>
  );
};
