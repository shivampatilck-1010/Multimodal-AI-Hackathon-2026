import { FileText, Presentation, Video, ArrowRight } from "lucide-react";
import type { MaterialItem } from "../types/dashboard";

interface CourseMaterialsProps {
  materials: MaterialItem[];
  onViewMaterials: () => void;
}

export const CourseMaterials: React.FC<CourseMaterialsProps> = ({
  materials,
  onViewMaterials,
}) => {
  const getIcon = (type: string) => {
    switch (type) {
      case "pdf":
        return <FileText size={18} style={{ color: "var(--primary-600)" }} aria-hidden="true" />;
      case "pptx":
        return <Presentation size={18} style={{ color: "#d97706" }} aria-hidden="true" />;
      case "video":
      default:
        return <Video size={18} style={{ color: "#dc2626" }} aria-hidden="true" />;
    }
  };

  return (
    <section className="card-surface" aria-labelledby="materials-heading">
      <div className="card-title-row">
        <h2 id="materials-heading" className="card-heading">
          Course Materials
        </h2>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Multimodal Source Base
        </span>
      </div>

      <div className="materials-list">
        {materials.map((item) => (
          <div key={item.id} className="material-item">
            {getIcon(item.type)}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {item.title}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                {item.detail}
              </div>
            </div>
            <span className="material-badge">{item.formatLabel}</span>
          </div>
        ))}
      </div>

      <button
        className="btn-secondary"
        style={{ width: "100%", justifyContent: "center", marginTop: "14px" }}
        onClick={onViewMaterials}
      >
        <span>View Materials</span>
        <ArrowRight size={15} />
      </button>
    </section>
  );
};
