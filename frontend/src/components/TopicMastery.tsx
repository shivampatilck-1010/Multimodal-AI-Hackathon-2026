import { CheckCircle2, AlertCircle, AlertTriangle, ChevronRight } from "lucide-react";
import type { TopicData, MasteryLevel } from "../types/dashboard";

interface TopicMasteryCardProps {
  topic: TopicData;
  onClick: (topic: TopicData) => void;
}

export const TopicMasteryCard: React.FC<TopicMasteryCardProps> = ({ topic, onClick }) => {
  const getStatusLabel = (level: MasteryLevel, pct: number) => {
    switch (level) {
      case "strong":
        return `Strong — ${pct}%`;
      case "developing":
        return `Developing — ${pct}%`;
      case "needs_attention":
      default:
        return `Needs attention — ${pct}%`;
    }
  };

  const getStatusIcon = (level: MasteryLevel) => {
    switch (level) {
      case "strong":
        return <CheckCircle2 size={14} aria-hidden="true" />;
      case "developing":
        return <AlertTriangle size={14} aria-hidden="true" />;
      case "needs_attention":
      default:
        return <AlertCircle size={14} aria-hidden="true" />;
    }
  };

  return (
    <div
      className="topic-card"
      onClick={() => onClick(topic)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick(topic);
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`Topic ${topic.name}, Status: ${getStatusLabel(topic.status, topic.masteryPercentage)}. Press Enter for concepts and sources.`}
    >
      <div className="topic-card-header">
        <span className="topic-name">{topic.name}</span>
        <span className={`topic-status-pill status-${topic.status}`}>
          {getStatusIcon(topic.status)}
          <span>{getStatusLabel(topic.status, topic.masteryPercentage)}</span>
        </span>
      </div>

      <div
        className="progress-track"
        role="progressbar"
        aria-valuenow={topic.masteryPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${topic.name} Mastery`}
      >
        <div
          className={`progress-fill fill-${topic.status}`}
          style={{ width: `${topic.masteryPercentage}%` }}
        />
      </div>

      <div className="topic-footer">
        <span>{topic.concepts.length} key concepts</span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
          View details <ChevronRight size={12} aria-hidden="true" />
        </span>
      </div>
    </div>
  );
};

interface TopicMasteryProps {
  topics: TopicData[];
  onSelectTopic: (topic: TopicData) => void;
}

export const TopicMastery: React.FC<TopicMasteryProps> = ({ topics, onSelectTopic }) => {
  return (
    <section className="card-surface" aria-labelledby="topic-mastery-heading">
      <div className="card-title-row">
        <h2 id="topic-mastery-heading" className="card-heading">
          Topic Mastery
        </h2>
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          Click a topic to view grounded sources & concepts
        </span>
      </div>

      <div className="topic-list">
        {topics.map((topic) => (
          <TopicMasteryCard key={topic.id} topic={topic} onClick={onSelectTopic} />
        ))}
      </div>
    </section>
  );
};
