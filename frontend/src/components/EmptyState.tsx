import React from "react";
import { FolderOpen } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No learning activity yet",
  message = "Complete your first study session or assessment to see your progress and topic mastery metrics.",
  actionLabel = "Start Learning",
  onAction,
}) => {
  return (
    <div className="state-container" role="status" aria-label="Empty course state">
      <div className="state-icon" aria-hidden="true">
        <FolderOpen size={28} />
      </div>
      <h2 className="state-title">{title}</h2>
      <p className="state-description">{message}</p>
      {onAction && (
        <button className="btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
};
