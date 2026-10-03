import { useState } from "react";
import type { MasteryHistoryPoint } from "../types/dashboard";

interface MasteryTrendProps {
  history: MasteryHistoryPoint[];
}

export const MasteryTrend: React.FC<MasteryTrendProps> = ({ history }) => {
  const [activePoint, setActivePoint] = useState<MasteryHistoryPoint | null>(null);

  if (!history || history.length === 0) return null;

  // Chart dimensions in viewBox coordinates
  const width = 500;
  const height = 180;
  const padding = { top: 20, right: 30, bottom: 35, left: 40 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const minVal = 30;
  const maxVal = 90;

  const points = history.map((pt, idx) => {
    const x = padding.left + (idx / (history.length - 1)) * plotWidth;
    const y = padding.top + plotHeight - ((pt.mastery - minVal) / (maxVal - minVal)) * plotHeight;
    return { ...pt, x, y };
  });

  const pathD = points.reduce((acc, curr, idx) => {
    return idx === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`;
  }, "");

  const areaD = `${pathD} L ${points[points.length - 1].x} ${padding.top + plotHeight} L ${points[0].x} ${padding.top + plotHeight} Z`;

  return (
    <section className="card-surface" aria-labelledby="mastery-trend-heading">
      <div className="card-title-row">
        <h2 id="mastery-trend-heading" className="card-heading">
          Mastery Trend
        </h2>
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {activePoint ? `${activePoint.period}: ${activePoint.mastery}% (${activePoint.label || ""})` : "5-week progression"}
        </span>
      </div>

      <div className="trend-chart-container">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: "100%", height: "100%", overflow: "visible" }}
          role="img"
          aria-label="Course mastery progression chart over 5 weeks"
        >
          {/* Y Axis Grid Lines */}
          {[40, 60, 80].map((level) => {
            const y = padding.top + plotHeight - ((level - minVal) / (maxVal - minVal)) * plotHeight;
            return (
              <g key={level}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="#94a3b8"
                  fontWeight="500"
                >
                  {level}%
                </text>
              </g>
            );
          })}

          {/* Shaded Area Under Curve */}
          <path d={areaD} fill="url(#trendGradient)" opacity={0.3} />

          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* Trend Line */}
          <path
            d={pathD}
            fill="none"
            stroke="#4f46e5"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points */}
          {points.map((pt, idx) => (
            <g key={idx}>
              <circle
                cx={pt.x}
                cy={pt.y}
                r={activePoint?.period === pt.period ? 6 : 4.5}
                fill={activePoint?.period === pt.period ? "#4338ca" : "#6366f1"}
                stroke="#ffffff"
                strokeWidth="2"
                style={{ cursor: "pointer", transition: "r 150ms ease" }}
                onMouseEnter={() => setActivePoint(pt)}
                onMouseLeave={() => setActivePoint(null)}
              />
              <text
                x={pt.x}
                y={padding.top + plotHeight + 20}
                textAnchor="middle"
                fontSize="11"
                fill="#64748b"
                fontWeight="600"
              >
                {pt.period}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        <span>Baseline: 42%</span>
        <span>Goal: 85% Mastery</span>
        <span style={{ color: "var(--success-text)", fontWeight: 600 }}>+26% Total Gain</span>
      </div>
    </section>
  );
};
