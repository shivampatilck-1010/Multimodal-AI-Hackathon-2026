import React from "react";
import { Sparkles, ArrowRight } from "lucide-react";

interface NewStudentStateProps {
  studentName: string;
  onStartDiagnostic: () => void;
}

export const NewStudentState: React.FC<NewStudentStateProps> = ({
  studentName,
  onStartDiagnostic,
}) => {
  return (
    <div className="state-container" role="region" aria-label="Welcome New Student">
      <div className="state-icon" style={{ backgroundColor: "var(--primary-50)", color: "var(--primary-600)" }}>
        <Sparkles size={28} />
      </div>
      <h2 className="state-title">Welcome to your course, {studentName} 👋</h2>
      <p className="state-description" style={{ fontSize: "1.05rem", lineHeight: 1.6 }}>
        Your personalized learning progress, topic mastery, and recommendations will appear here after you complete your initial diagnostic assessment.
      </p>
      <button className="btn-primary" style={{ padding: "10px 22px", fontSize: "0.95rem" }} onClick={onStartDiagnostic}>
        <span>Start Diagnostic</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
};
