import React, { useState, useEffect } from "react";
import { ArrowLeft, BookOpen, Layers, Video } from "lucide-react";

interface ContentUnitItem {
  id: string;
  text: string;
  topic: string;
  concept: string;
  source: {
    type: string;
    file_name: string;
    page?: number;
    slide?: number;
    timestamp_start?: string;
  };
}

export const MaterialsPage: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [units, setUnits] = useState<ContentUnitItem[]>([
    {
      id: "unit_1",
      topic: "Optimization",
      concept: "Gradient Descent",
      text: "Gradient descent is an iterative optimization algorithm for finding a local minimum of a differentiable function. The step size is scaled by the learning rate parameter alpha.",
      source: { type: "pdf", file_name: "machine_learning_foundations.pdf", page: 12 },
    },
    {
      id: "unit_2",
      topic: "Neural Networks",
      concept: "Backpropagation",
      text: "Backpropagation recursively applies the chain rule of calculus to compute gradient vectors with respect to weight parameters across successive network layers.",
      source: { type: "slide", file_name: "lecture_slides_week3.pptx", slide: 15 },
    },
    {
      id: "unit_3",
      topic: "Optimization",
      concept: "Momentum",
      text: "Momentum accelerates gradient descent by navigating directions with consistent gradient signs while damping oscillations across ravines in parameter space.",
      source: { type: "video", file_name: "lecture_recording_04.mp4", timestamp_start: "00:14:20" },
    },
  ]);

  useEffect(() => {
    fetch("http://localhost:8000/api/kb/courses/hackathon_course/units")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setUnits(data);
        }
      })
      .catch((e) => console.log("Using cached materials:", e));
  }, []);

  const filteredUnits = units.filter((u) => {
    if (filter !== "all" && u.source.type !== filter) return false;
    if (search && !u.text.toLowerCase().includes(search.toLowerCase()) && !u.concept?.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto", padding: "24px 16px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
        <button className="new-btn-primary" onClick={onBack} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", cursor: "pointer" }}>
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>
        <span style={{ fontSize: "0.85rem", color: "#a3a3a3", border: "1px solid #333", padding: "4px 12px", borderRadius: "16px" }}>
          Member 1 • Multimodal Knowledge Base Units
        </span>
      </div>

      {/* Controls */}
      <div className="card-surface" style={{ padding: "20px", borderRadius: "12px", border: "1px solid #333", marginBottom: "24px" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, margin: "0 0 16px 0" }}>Multimodal Course Materials</h1>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ flex: 1, minWidth: "240px" }}>
            <input
              type="text"
              placeholder="Search extracted passages or concepts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: "100%", padding: "10px 14px", background: "#000", border: "1px solid #444", borderRadius: "8px", color: "#fff" }}
            />
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            {["all", "pdf", "slide", "video"].map((t) => (
              <button
                key={t}
                onClick={() => setFilter(t)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: filter === t ? "#333333" : "#111111",
                  color: "#ffffff",
                  border: filter === t ? "1px solid #777777" : "1px solid #444444",
                  fontWeight: 600,
                  fontSize: "0.85rem",
                  cursor: "pointer",
                }}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* List of Units */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredUnits.map((u) => (
          <div key={u.id} className="card-surface" style={{ padding: "20px", borderRadius: "12px", border: "1px solid #333" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {u.source.type === "pdf" && <BookOpen size={18} color="#3b82f6" />}
                {u.source.type === "slide" && <Layers size={18} color="#a855f7" />}
                {u.source.type === "video" && <Video size={18} color="#ef4444" />}
                <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                  {u.concept || u.topic || "Course Excerpt"}
                </span>
              </div>

              <span style={{ fontSize: "0.75rem", background: "#1a1a1a", border: "1px solid #333", padding: "4px 10px", borderRadius: "4px", color: "#e5e5e5" }}>
                {u.source.file_name} • {u.source.page ? `Page ${u.source.page}` : (u.source.slide ? `Slide ${u.source.slide}` : u.source.timestamp_start)}
              </span>
            </div>

            <p style={{ color: "#d4d4d4", fontSize: "0.92rem", lineHeight: 1.6, margin: 0 }}>
              {u.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
