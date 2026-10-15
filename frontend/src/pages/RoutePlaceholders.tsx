
import React, { useEffect, useRef, useState } from "react";
import {
  Bot,
  FileCheck2,
  TrendingUp,
  FolderGit2,
  Network,
  Settings,
  ArrowLeft,
  Send,
  BookOpen,
  ExternalLink,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  MessageSquare,
} from "lucide-react";
import { askTutor, type TutorCitation } from "../client";

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
}) => (
  <div
    className="card-surface"
    style={{
      padding: "48px 32px",
      textAlign: "center",
      maxWidth: "640px",
      margin: "40px auto",
    }}
  >
    <div
      style={{
        width: 56,
        height: 56,
        borderRadius: "50%",
        background: "var(--primary-50)",
        color: "var(--primary-600)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        margin: "0 auto 16px",
      }}
    >
      {icon}
    </div>

    <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>
      {title}
    </h1>

    <p
      style={{
        color: "var(--text-secondary)",
        fontSize: "0.95rem",
        lineHeight: 1.6,
        marginBottom: 16,
      }}
    >
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
        marginBottom: 24,
      }}
    >
      Owned by {memberOwner} · Frontend integration ready
    </div>

    <div>
      <button className="btn-primary" onClick={onBackToDashboard}>
        <ArrowLeft size={16} />
        <span>Back to Student Dashboard</span>
      </button>
    </div>
  </div>
);

interface TutorMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  grounded?: boolean;
  citations?: TutorCitation[];
  unsupportedReason?: string | null;
  outsideKnowledge?: string | null;
  relatedTopics?: string[];
}

const createSessionId = () =>
  `tutor-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const getSessionId = (): string => {
  try {
    const existing = sessionStorage.getItem("multimodal-tutor-session");
    if (existing) return existing;

    const sessionId = createSessionId();
    sessionStorage.setItem("multimodal-tutor-session", sessionId);
    return sessionId;
  } catch {
    return createSessionId();
  }
};

const citationUrl = (citation: TutorCitation): string | null => {
  const link = citation.link?.trim();
  if (!link) return null;

  if (/^https?:\/\//i.test(link)) return link;

  // API routes are served by the local backend.
  const backendBase = "http://127.0.0.1:8080";

  if (link.startsWith("/")) return `${backendBase}${link}`;
  return `${backendBase}/${link}`;
};

const CitationCard: React.FC<{ citation: TutorCitation }> = ({ citation }) => {
  const href = citationUrl(citation);

  let location = citation.location || "";
  if (citation.slide != null) location = `Slide ${citation.slide}`;
  if (citation.page != null) location = `Page ${citation.page}`;
  if (citation.timestamp_start) {
    location = citation.timestamp_end
      ? `${citation.timestamp_start} – ${citation.timestamp_end}`
      : citation.timestamp_start;
  }

  return (
    <div
      style={{
        border: "1px solid var(--border-color, #e2e8f0)",
        borderRadius: 10,
        padding: 12,
        marginTop: 8,
        background: "var(--surface-secondary, #f8fafc)",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <BookOpen
          size={17}
          style={{
            flexShrink: 0,
            marginTop: 2,
            color: "var(--primary-600)",
          }}
        />

        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>
            {citation.label || "Course evidence"} ·{" "}
            {citation.concept || citation.topic || "Course source"}
          </div>

          <div
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.8rem",
              marginTop: 3,
              overflowWrap: "anywhere",
            }}
          >
            {citation.file_name || "Source filename unavailable"}
            {location ? ` · ${location}` : ""}
          </div>

          {citation.excerpt && (
            <p
              style={{
                fontSize: "0.82rem",
                lineHeight: 1.5,
                margin: "8px 0 0",
                color: "var(--text-secondary)",
              }}
            >
              {citation.excerpt}
            </p>
          )}

          {href ? (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                marginTop: 9,
                color: "var(--primary-600)",
                fontSize: "0.82rem",
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              Open source <ExternalLink size={13} />
            </a>
          ) : (
            <div
              style={{
                marginTop: 9,
                color: "var(--text-secondary)",
                fontSize: "0.78rem",
              }}
            >
              Source link unavailable; citation metadata is shown above.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const TutorMessageBubble: React.FC<{ message: TutorMessage }> = ({
  message,
}) => {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        gap: 10,
        alignItems: "flex-start",
        marginBottom: 22,
      }}
    >
      {!isUser && (
        <div
          style={{
            width: 34,
            height: 34,
            flexShrink: 0,
            borderRadius: 10,
            background: "var(--primary-50)",
            color: "var(--primary-600)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Bot size={19} />
        </div>
      )}

      <div
        style={{
          maxWidth: isUser ? "82%" : "90%",
          minWidth: 0,
          borderRadius: 14,
          padding: "14px 16px",
          background: isUser
            ? "var(--primary-600, #2563eb)"
            : "var(--surface-primary, #ffffff)",
          color: isUser ? "#ffffff" : "var(--text-primary, #1e293b)",
          border: isUser
            ? "none"
            : "1px solid var(--border-color, #e2e8f0)",
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <div
          style={{
            whiteSpace: "pre-wrap",
            overflowWrap: "anywhere",
            lineHeight: 1.7,
            fontSize: "0.93rem",
          }}
        >
          {message.content}
        </div>

        {!isUser && message.grounded !== undefined && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.77rem",
              marginTop: 12,
              color: message.grounded ? "#15803d" : "#b45309",
            }}
          >
            {message.grounded ? (
              <CheckCircle2 size={15} />
            ) : (
              <AlertCircle size={15} />
            )}
            {message.grounded
              ? "Grounded in course material"
              : "No sufficient supporting course evidence"}
          </div>
        )}

        {!isUser && message.unsupportedReason && (
          <p
            style={{
              margin: "8px 0 0",
              fontSize: "0.82rem",
              color: "var(--text-secondary)",
            }}
          >
            {message.unsupportedReason}
          </p>
        )}

        {!isUser && message.outsideKnowledge && (
          <div
            style={{
              marginTop: 12,
              padding: 10,
              borderLeft: "3px solid #d97706",
              background: "var(--surface-secondary, #fffbeb)",
              fontSize: "0.85rem",
              lineHeight: 1.6,
            }}
          >
            <strong>Outside course material</strong>
            <p style={{ margin: "5px 0 0" }}>{message.outsideKnowledge}</p>
          </div>
        )}

        {!isUser && !!message.citations?.length && (
          <div style={{ marginTop: 14 }}>
            <div
              style={{
                fontWeight: 700,
                fontSize: "0.82rem",
                marginBottom: 8,
              }}
            >
              Sources ({message.citations.length})
            </div>
            {message.citations.map((citation, index) => (
              <CitationCard
                key={`${citation.source_id}-${citation.label}-${index}`}
                citation={citation}
              />
            ))}
          </div>
        )}

        {!isUser && !!message.relatedTopics?.length && (
          <div
            style={{
              display: "flex",
              gap: 6,
              flexWrap: "wrap",
              marginTop: 12,
            }}
          >
            {message.relatedTopics.map((topic) => (
              <span
                key={topic}
                style={{
                  borderRadius: 20,
                  padding: "4px 9px",
                  fontSize: "0.76rem",
                  background: "var(--primary-50)",
                  color: "var(--primary-700)",
                }}
              >
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const TutorPage: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const [messages, setMessages] = useState<TutorMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Ask me about your course material. I’ll use available lecture slides, videos, and notes, and show source citations when evidence is available.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [level, setLevel] = useState("intermediate");
  const [error, setError] = useState("");
  const [sessionId] = useState(getSessionId);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const sendMessage = async (text = input) => {
    const query = text.trim();
    if (!query || loading) return;

    setError("");
    setInput("");
    setMessages((previous) => [
      ...previous,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: query,
      },
    ]);
    setLoading(true);

    try {
      const response = await askTutor(query, "cs229", sessionId, level);

      setMessages((previous) => [
        ...previous,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          grounded: response.grounded,
          citations: response.citations || [],
          unsupportedReason: response.unsupported_reason,
          outsideKnowledge: response.outside_knowledge,
          relatedTopics: response.related_topics || [],
        },
      ]);
    } catch (err) {
      const detail =
        err instanceof Error ? err.message : "Unexpected error occurred";
      setError(
        `Unable to reach the tutor service: ${detail}. Check that the backend is running and try again.`,
      );
      setInput(query);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const suggestions = [
    "Explain gradient descent simply",
    "What is backpropagation?",
    "Explain linear regression",
  ];

  return (
    <div
      style={{
        maxWidth: 1040,
        margin: "0 auto",
        padding: "24px 20px 32px",
        minHeight: "calc(100vh - 100px)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          flexWrap: "wrap",
          marginBottom: 22,
        }}
      >
        <div>
          <button
            type="button"
            onClick={onBack}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              border: "none",
              background: "transparent",
              color: "var(--text-secondary)",
              padding: "4px 0",
              cursor: "pointer",
              marginBottom: 14,
              fontSize: "0.86rem",
            }}
          >
            <ArrowLeft size={16} /> Back to dashboard
          </button>

          <h1
            style={{
              fontSize: "clamp(1.45rem, 3vw, 2rem)",
              fontWeight: 750,
              margin: 0,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <Bot size={27} /> AI Tutor
          </h1>

          <p
            style={{
              color: "var(--text-secondary)",
              margin: "8px 0 0",
              fontSize: "0.9rem",
              lineHeight: 1.6,
            }}
          >
            Course-grounded explanations with source citations.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <label
            htmlFor="tutor-level"
            style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}
          >
            Explanation level
          </label>
          <select
            id="tutor-level"
            value={level}
            onChange={(event) => setLevel(event.target.value)}
            disabled={loading}
            style={{
              border: "1px solid var(--border-color, #cbd5e1)",
              borderRadius: 9,
              padding: "9px 11px",
              background: "var(--surface-primary, #ffffff)",
              color: "var(--text-primary, #1e293b)",
              fontSize: "0.85rem",
            }}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </div>

      <div
        className="card-surface"
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          minHeight: 520,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "15px 18px",
            borderBottom: "1px solid var(--border-color, #e2e8f0)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "var(--primary-50)",
              color: "var(--primary-600)",
            }}
          >
            <MessageSquare size={18} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.92rem" }}>
              Course assistant
            </div>
            <div
              style={{
                fontSize: "0.77rem",
                color: "var(--text-secondary)",
                marginTop: 3,
              }}
            >
              CS229 · Answers checked against retrieved course evidence
            </div>
          </div>
        </div>

        <div
          style={{
            flex: 1,
            padding: "22px 18px",
            overflowY: "auto",
            minHeight: 300,
            maxHeight: "calc(100vh - 350px)",
          }}
        >
          {messages.map((message) => (
            <TutorMessageBubble key={message.id} message={message} />
          ))}

          {loading && (
            <div
              role="status"
              aria-live="polite"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 9,
                color: "var(--text-secondary)",
                fontSize: "0.87rem",
                padding: "8px 0 16px",
              }}
            >
              <LoaderCircle size={17} className="tutor-spinner" />
              Searching course material and preparing an answer…
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {messages.length === 1 && (
          <div
            style={{
              padding: "0 18px 16px",
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
            }}
          >
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => void sendMessage(suggestion)}
                disabled={loading}
                style={{
                  border: "1px solid var(--border-color, #cbd5e1)",
                  borderRadius: 20,
                  padding: "8px 12px",
                  background: "var(--surface-primary, #ffffff)",
                  color: "var(--text-primary, #334155)",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontSize: "0.81rem",
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div
            role="alert"
            style={{
              display: "flex",
              gap: 8,
              alignItems: "flex-start",
              margin: "0 18px 12px",
              padding: "11px 12px",
              borderRadius: 9,
              background: "#fef2f2",
              color: "#b91c1c",
              fontSize: "0.83rem",
              lineHeight: 1.5,
            }}
          >
            <AlertCircle size={17} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{error}</span>
          </div>
        )}

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void sendMessage();
          }}
          style={{
            padding: "14px 18px 18px",
            borderTop: "1px solid var(--border-color, #e2e8f0)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 10,
              border: "1px solid var(--border-color, #cbd5e1)",
              borderRadius: 13,
              padding: "8px 8px 8px 13px",
              background: "var(--surface-primary, #ffffff)",
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
              placeholder="Ask a question about your course…"
              aria-label="Ask the AI tutor"
              rows={2}
              disabled={loading}
              style={{
                flex: 1,
                resize: "vertical",
                minHeight: 44,
                maxHeight: 160,
                border: "none",
                outline: "none",
                background: "transparent",
                color: "var(--text-primary, #1e293b)",
                font: "inherit",
                fontSize: "0.91rem",
                lineHeight: 1.5,
                padding: "8px 0",
              }}
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
              aria-label="Send message"
              title="Send message"
              style={{
                width: 42,
                height: 42,
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "none",
                borderRadius: 10,
                background:
                  loading || !input.trim()
                    ? "var(--border-color, #cbd5e1)"
                    : "var(--primary-600, #2563eb)",
                color: "#ffffff",
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? (
                <LoaderCircle size={18} className="tutor-spinner" />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              flexWrap: "wrap",
              color: "var(--text-secondary)",
              fontSize: "0.74rem",
              marginTop: 9,
            }}
          >
            <span>Enter to send · Shift + Enter for a new line</span>
            <span>Answers depend on available course evidence</span>
          </div>
        </form>
      </div>
    </div>
  );
};

export const AssessmentsPage: React.FC<{ onBack: () => void }> = ({
  onBack,
}) => (
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
