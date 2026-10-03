import { Award, TrendingUp, HelpCircle, Clock } from "lucide-react";
import type { SummaryMetric } from "../types/dashboard";

interface SummaryCardProps {
  title: string;
  value: string;
  subtitle: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  iconName: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  iconName,
}) => {
  const renderIcon = () => {
    switch (iconName) {
      case "award":
        return <Award size={18} />;
      case "trending-up":
        return <TrendingUp size={18} />;
      case "help-circle":
        return <HelpCircle size={18} />;
      case "clock":
      default:
        return <Clock size={18} />;
    }
  };

  return (
    <div className="summary-card" role="region" aria-label={title}>
      <div className="summary-card-header">
        <span className="summary-card-title">{title}</span>
        <div className="summary-card-icon" aria-hidden="true">
          {renderIcon()}
        </div>
      </div>
      <div className="summary-card-value">{value}</div>
      <div className="summary-card-footer">
        <span className="summary-card-subtitle">{subtitle}</span>
        {trend && <span className="summary-card-trend">{trend}</span>}
      </div>
    </div>
  );
};

interface SummaryCardsProps {
  metrics: SummaryMetric[];
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ metrics }) => {
  return (
    <section className="summary-grid" aria-label="Learning Metrics Overview">
      {metrics.map((metric) => (
        <SummaryCard
          key={metric.id}
          title={metric.title}
          value={metric.value}
          subtitle={metric.subtitle}
          trend={metric.trend}
          trendDirection={metric.trendDirection}
          iconName={metric.iconName}
        />
      ))}
    </section>
  );
};
