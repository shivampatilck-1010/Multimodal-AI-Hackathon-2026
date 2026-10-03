import React, { useEffect } from "react";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Presentation,
  Video,
  Bot,
  HelpCircle,
  BookOpen,
} from "lucide-react";
import type { TopicData } from "../types/dashboard";

interface TopicDetailModalProps {
  topic: TopicData | null;
  onClose: () => void;
  onActionClick: (actionName: string) => void;
}

export const TopicDetailModal: React.FC<TopicDetailModalProps> = ({
  topic,
  onClose,
  onActionClick,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!topic) return null;

  const renderSourceIcon = (type: string) => {
    switch (type) {
      case "textbook":
        return <FileText size={16} aria-hidden="true" style={{ color: "var(--primary-600)" }} />;
      case "slide":
        return <Presentation size={16} aria-hidden="true" style={{ color: "#d97706" }} />;
      case "video":
      default:
        return <Video size={16} aria-hidden="true" style={{ color: "#dc2626" }} />;
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-topic-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close topic details"
        >
          <X size={20} />
        </button>

        <h2 id="modal-topic-title" style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "4px" }}>
          {topic.name}
        </h2>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
          <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>Mastery Level:</span>
          <span
            className={`topic-status-pill status-${topic.status}`}
            style={{ fontSize: "0.85rem", padding: "4px 10px" }}
          >
            {topic.masteryPercentage}%
          </span>
        </div>

        <div style={{ marginBottom: "22px" }}>
          <h3
            style={{
              fontSize: "0.9rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: "10px",
              fontWeight: 700,
            }}
          >
            Concepts Breakdown
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {topic.concepts.map((concept) => (
              <div
                key={concept.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontSize: "0.9rem",
                  padding: "6px 10px",
                  borderRadius: "var(--border-radius-sm)",
                  background: concept.status === "needs_work" ? "#fff8f8" : "var(--bg-subtle)",
                }}
              >
                {concept.status === "mastered" ? (
                  <CheckCircle2 size={16} style={{ color: "var(--success-bar)", flexShrink: 0 }} />
                ) : (
                  <AlertTriangle size={16} style={{ color: "var(--warning-bar)", flexShrink: 0 }} />
                )}
                <span
                  style={{
                    color: concept.status === "needs_work" ? "var(--danger-text)" : "var(--text-primary)",
                    fontWeight: concept.status === "needs_work" ? 600 : 400,
                  }}
                >
                  {concept.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: "26px" }}>
          <h3
            style={{
              fontSize: "0.9rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: "10px",
              fontWeight: 700,
            }}
          >
            Course Sources & Provenance
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {topic.sources.map((src, idx) => (
              <div key={idx} className="source-item">
                {renderSourceIcon(src.type)}
                <span>
                  <strong>{src.label}</strong> — {src.location}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="btn-group" style={{ paddingTop: "12px", borderTop: "1px solid var(--border-light)" }}>
          <button
            className="btn-primary"
            onClick={() => onActionClick(`Ask Tutor about ${topic.name}`)}
          >
            <Bot size={16} />
            Ask Tutor
          </button>
          <button
            className="btn-secondary"
            onClick={() => onActionClick(`Practice Questions on ${topic.name}`)}
          >
            <HelpCircle size={16} />
            Practice Questions
          </button>
          <button
            className="btn-secondary"
            onClick={() => onActionClick(`Review Material for ${topic.name}`)}
          >
            <BookOpen size={16} />
            Review Material
          </button>
        </div>
      </div>
    </div>
  );
};
