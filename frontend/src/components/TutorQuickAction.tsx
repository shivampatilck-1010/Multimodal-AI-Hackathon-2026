import React from "react";
import { Bot, ArrowRight } from "lucide-react";

interface TutorQuickActionProps {
  onAskTutor: (prompt?: string) => void;
}

export const TutorQuickAction: React.FC<TutorQuickActionProps> = ({ onAskTutor }) => {
  const examplePrompt = "Explain gradient descent simply";

  return (
    <section className="card-surface quick-tutor-card" aria-labelledby="quick-tutor-title">
      <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--primary-700)", fontWeight: 700, fontSize: "0.9rem" }}>
        <Bot size={18} aria-hidden="true" />
        <span id="quick-tutor-title">Ask about your course...</span>
      </div>

      <div className="quick-tutor-prompt">
        "{examplePrompt}"
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          className="btn-primary"
          onClick={() => onAskTutor(examplePrompt)}
          aria-label="Ask Tutor: Explain gradient descent simply"
        >
          <span>Ask Tutor</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </section>
  );
};
