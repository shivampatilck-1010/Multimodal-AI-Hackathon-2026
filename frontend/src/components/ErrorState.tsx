import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = "Unable to load dashboard data.",
  onRetry,
}) => {
  return (
    <div className="state-container" role="alert" aria-live="assertive">
      <div className="state-icon" style={{ backgroundColor: "var(--danger-bg)", color: "var(--danger-bar)" }}>
        <AlertCircle size={28} />
      </div>
      <h2 className="state-title">{message}</h2>
      <p className="state-description">
        We encountered an issue retrieving your course progress. Please check your network connection and retry.
      </p>
      <button className="btn-primary" onClick={onRetry}>
        <RotateCcw size={16} />
        <span>Retry</span>
      </button>
    </div>
  );
};
