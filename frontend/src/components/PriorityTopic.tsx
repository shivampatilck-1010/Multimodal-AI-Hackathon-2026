import { AlertTriangle, BookOpen, Target } from "lucide-react";
import type { PriorityTopicData } from "../types/dashboard";

interface PriorityTopicProps {
  priority: PriorityTopicData;
  onReview: (topicName: string) => void;
  onPractice: (topicName: string) => void;
}

export const PriorityTopic: React.FC<PriorityTopicProps> = ({
  priority,
  onReview,
  onPractice,
}) => {
  return (
    <section className="card-surface priority-card" aria-labelledby="priority-topic-title">
      <div className="priority-header">
        <AlertTriangle size={18} aria-hidden="true" />
        <span>Priority Topic</span>
      </div>

      <div className="priority-title">{priority.topicName}</div>
      <div className="priority-mastery">
        Current Mastery: {priority.masteryPercentage}% (Needs Attention)
      </div>

      <p className="priority-message">{priority.message}</p>

      <div className="btn-group">
        <button
          className="btn-primary"
          style={{ backgroundColor: "var(--danger-bar)" }}
          onClick={() => onReview(priority.topicName)}
        >
          <BookOpen size={16} />
          Review Topic
        </button>
        <button
          className="btn-secondary"
          onClick={() => onPractice(priority.topicName)}
        >
          <Target size={16} />
          Practice
        </button>
      </div>
    </section>
  );
};
