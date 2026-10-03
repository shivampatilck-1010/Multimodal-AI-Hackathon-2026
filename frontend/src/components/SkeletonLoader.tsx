import React from "react";

export const SkeletonLoader: React.FC = () => {
  return (
    <div aria-label="Loading dashboard data..." aria-busy="true">
      {/* Summary Skeletons */}
      <div className="summary-grid" style={{ marginBottom: "28px" }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="summary-card" style={{ gap: "12px" }}>
            <div className="skeleton" style={{ width: "40%", height: "14px" }} />
            <div className="skeleton" style={{ width: "60%", height: "36px" }} />
            <div className="skeleton" style={{ width: "50%", height: "12px" }} />
          </div>
        ))}
      </div>

      {/* Main Grid Skeletons */}
      <div className="dashboard-main-grid">
        <div className="dashboard-left-col">
          <div className="card-surface" style={{ height: "300px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div className="skeleton" style={{ width: "30%", height: "24px" }} />
            <div className="skeleton" style={{ width: "100%", height: "54px" }} />
            <div className="skeleton" style={{ width: "100%", height: "54px" }} />
            <div className="skeleton" style={{ width: "100%", height: "54px" }} />
          </div>
          <div className="card-surface" style={{ height: "220px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div className="skeleton" style={{ width: "25%", height: "24px" }} />
            <div className="skeleton" style={{ width: "100%", height: "120px" }} />
          </div>
        </div>

        <div className="dashboard-right-col">
          <div className="card-surface" style={{ height: "180px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className="skeleton" style={{ width: "40%", height: "20px" }} />
            <div className="skeleton" style={{ width: "70%", height: "24px" }} />
            <div className="skeleton" style={{ width: "100%", height: "36px" }} />
          </div>
          <div className="card-surface" style={{ height: "240px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className="skeleton" style={{ width: "50%", height: "20px" }} />
            <div className="skeleton" style={{ width: "40%", height: "40px" }} />
            <div className="skeleton" style={{ width: "100%", height: "60px" }} />
          </div>
        </div>
      </div>
    </div>
  );
};
