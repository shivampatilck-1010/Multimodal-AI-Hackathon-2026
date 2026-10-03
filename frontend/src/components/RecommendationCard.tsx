import { Compass, BookOpen, Target, Bot } from "lucide-react";
import type { RecommendationData } from "../types/dashboard";

interface RecommendationCardProps {
  recommendation: RecommendationData;
  onAction: (actionName: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onAction,
}) => {
  return (
    <section className="card-surface recommendation-card" aria-labelledby="recommendation-heading">
      <div className="recommendation-header">
        <Compass size={16} aria-hidden="true" />
        <span id="recommendation-heading">Recommended Next</span>
      </div>

      <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "6px 0" }}>
        🎯 {recommendation.title}
      </h3>

      <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
        {recommendation.reason}
      </p>

      <div className="btn-group">
        <button
          className="btn-primary"
          onClick={() => onAction(`Review ${recommendation.conceptName}`)}
        >
          <BookOpen size={15} />
          Review
        </button>
        <button
          className="btn-secondary"
          onClick={() => onAction(`Practice ${recommendation.conceptName}`)}
        >
          <Target size={15} />
          Practice
        </button>
        <button
          className="btn-secondary"
          onClick={() => onAction(`Ask Tutor about ${recommendation.conceptName}`)}
        >
          <Bot size={15} />
          Ask Tutor
        </button>
      </div>
    </section>
  );
};
