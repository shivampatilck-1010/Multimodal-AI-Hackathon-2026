
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
  LoaderCircle,
} from "lucide-react";
import type { TopicData } from "../types/dashboard";
import type { ConceptEvidence } from "../client";

interface TopicDetailModalProps {
  topic: TopicData | null;
  evidence: ConceptEvidence | null;
  evidenceLoading: boolean;
  evidenceError: string | null;
  onClose: () => void;
  onActionClick: (actionName: string) => void | Promise<void>;
}

function sourceIcon(type: string) {
  switch (type.toLowerCase()) {
    case "pdf":
    case "textbook":
      return <FileText size={17} aria-hidden="true" />;
    case "slide":
    case "pptx":
      return <Presentation size={17} aria-hidden="true" />;
    case "video":
      return <Video size={17} aria-hidden="true" />;
    default:
      return <FileText size={17} aria-hidden="true" />;
  }
}

function sourceLocation(unit: ConceptEvidence["units"][number]): string {
  const source = unit.source;
  const type = source.type.toLowerCase();

  if (type === "pdf" && source.page != null) {
    return `Page ${source.page}`;
  }

  if ((type === "slide" || type === "pptx") && source.slide != null) {
    return `Slide ${source.slide}`;
  }

  if (type === "video") {
    if (source.timestamp_start && source.timestamp_end) {
      return `${source.timestamp_start}–${source.timestamp_end}`;
    }

    if (source.start_seconds != null) {
      return `Starts at ${Math.floor(source.start_seconds / 60)}:${String(
        Math.floor(source.start_seconds % 60),
      ).padStart(2, "0")}`;
    }
  }

  return unit.subtopic || unit.topic || "Course material";
}

export const TopicDetailModal: React.FC<TopicDetailModalProps> = ({
  topic,
  evidence,
  evidenceLoading,
  evidenceError,
  onClose,
  onActionClick,
}) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!topic) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-topic-title"
    >
      <div className="modal-content" onClick={(event) => event.stopPropagation()}>
        <button
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close topic details"
          type="button"
        >
          <X size={20} />
        </button>

        <h2
          id="modal-topic-title"
          style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: 4 }}
        >
          {topic.name}
        </h2>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 20,
          }}
        >
          <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
            Mastery Level:
          </span>
          <span
            className={`topic-status-pill status-${topic.status}`}
            style={{ fontSize: "0.85rem", padding: "4px 10px" }}
          >
            {topic.masteryPercentage}%
          </span>
        </div>

        <section style={{ marginBottom: 22 }}>
          <h3
            style={{
              fontSize: "0.9rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            Concepts Breakdown
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {topic.concepts.map((concept) => (
              <div
                key={concept.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: "0.9rem",
                  padding: "6px 10px",
                  borderRadius: "var(--border-radius-sm)",
                  background:
                    concept.status === "needs_work"
                      ? "#fff8f8"
                      : "var(--bg-subtle)",
                }}
              >
                {concept.status === "mastered" ? (
                  <CheckCircle2
                    size={16}
                    style={{ color: "var(--success-bar)", flexShrink: 0 }}
                  />
                ) : (
                  <AlertTriangle
                    size={16}
                    style={{ color: "var(--warning-bar)", flexShrink: 0 }}
                  />
                )}
                <span
                  style={{
                    color:
                      concept.status === "needs_work"
                        ? "var(--danger-text)"
                        : "var(--text-primary)",
                    fontWeight: concept.status === "needs_work" ? 600 : 400,
                  }}
                >
                  {concept.name}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section style={{ marginBottom: 22 }}>
          <h3
            style={{
              fontSize: "0.9rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            Course Sources &amp; Provenance
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {topic.sources.map((source, index) => (
              <div key={`${source.label}-${index}`} className="source-item">
                {sourceIcon(source.type)}
                <span>
                  <strong>{source.label}</strong> — {source.location}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section style={{ marginBottom: 22 }}>
          <h3
            style={{
              fontSize: "0.9rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-secondary)",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            Retrieved Course Evidence
          </h3>

          {evidenceLoading && (
            <div role="status" style={{ display: "flex", gap: 8, padding: 12 }}>
              <LoaderCircle size={18} />
              <span>Loading course evidence…</span>
            </div>
          )}

          {!evidenceLoading && evidenceError && (
            <p role="alert" style={{ padding: 12, color: "var(--danger-text)" }}>
              {evidenceError}
            </p>
          )}

          {!evidenceLoading && evidence && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                {evidence.concept.name}
                {evidence.units.length > 0
                  ? ` · ${evidence.units.length} source unit(s)`
                  : ""}
              </p>

              {evidence.concept.summary && (
                <p style={{ lineHeight: 1.6 }}>{evidence.concept.summary}</p>
              )}

              {evidence.units.map((unit) => (
                <article
                  key={unit.id}
                  style={{
                    border: "1px solid var(--border-light)",
                    borderRadius: "var(--border-radius-sm)",
                    padding: 12,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 8,
                    }}
                  >
                    {sourceIcon(unit.source.type)}
                    <strong style={{ overflowWrap: "anywhere" }}>
                      {unit.source.file_name}
                    </strong>
                  </div>

                  <p
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--text-secondary)",
                      marginBottom: 8,
                    }}
                  >
                    {sourceLocation(unit)}
                  </p>

                  <p style={{ lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                    {unit.text}
                  </p>
                </article>
              ))}

              {evidence.figures.map((figure, index) => (
                <article
                  key={figure.id ?? `figure-${index}`}
                  style={{
                    border: "1px solid var(--border-light)",
                    borderRadius: "var(--border-radius-sm)",
                    padding: 12,
                  }}
                >
                  {figure.caption && <strong>{figure.caption}</strong>}
                  {figure.explanation && <p>{figure.explanation}</p>}
                </article>
              ))}

              {evidence.units.length === 0 &&
                evidence.figures.length === 0 && (
                  <p>No source material is linked to this concept yet.</p>
                )}
            </div>
          )}
        </section>

        <div
          className="btn-group"
          style={{
            paddingTop: 12,
            borderTop: "1px solid var(--border-light)",
          }}
        >
          <button
            className="btn-primary"
            type="button"
            onClick={() => void onActionClick(`Ask Tutor about ${topic.name}`)}
          >
            <Bot size={16} />
            Ask Tutor
          </button>

          <button
            className="btn-secondary"
            type="button"
            onClick={() =>
              void onActionClick(`Practice Questions on ${topic.name}`)
            }
          >
            <HelpCircle size={16} />
            Practice Questions
          </button>

          <button
            className="btn-secondary"
            type="button"
            onClick={() =>
              void onActionClick(`Review Material for ${topic.name}`)
            }
          >
            <BookOpen size={16} />
            Review Material
          </button>
        </div>
      </div>
    </div>
  );
};
