import { useState } from "react";
import type { ActivityDay } from "../types/dashboard";

interface LearningActivityProps {
  activity: ActivityDay[];
}

export const LearningActivity: React.FC<LearningActivityProps> = ({ activity }) => {
  const [hoveredDay, setHoveredDay] = useState<ActivityDay | null>(null);

  const maxHours = Math.max(...activity.map((a) => a.hours), 5);

  return (
    <section className="card-surface" aria-labelledby="activity-heading">
      <div className="card-title-row">
        <h2 id="activity-heading" className="card-heading">
          Learning Activity
        </h2>
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {hoveredDay ? `${hoveredDay.day} (${hoveredDay.dateStr}): ${hoveredDay.hours} hrs` : "Past 7 days"}
        </span>
      </div>

      <div className="activity-bars" role="region" aria-label="Weekly study hours chart">
        {activity.map((item) => {
          const heightPercent = (item.hours / maxHours) * 100;
          return (
            <div
              key={item.day}
              className="activity-bar-col"
              onMouseEnter={() => setHoveredDay(item)}
              onMouseLeave={() => setHoveredDay(null)}
            >
              <div
                className="activity-bar-fill"
                style={{ height: `${Math.max(heightPercent, 8)}%` }}
                title={`${item.day}: ${item.hours} hours`}
                role="img"
                aria-label={`${item.day}: ${item.hours} hours study`}
              />
              <span className="activity-day-label">{item.day}</span>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        <span>0 hrs</span>
        <span>Average: 2.7 hrs/day</span>
        <span>Peak: 4.2 hrs</span>
      </div>
    </section>
  );
};
