import {
  LayoutDashboard,
  Bot,
  FileCheck2,
  TrendingUp,
  FolderGit2,
  Network,
  Settings,
} from "lucide-react";
import type { NavRoute } from "../types/dashboard";

interface SidebarProps {
  currentRoute: NavRoute;
  onNavigate: (route: NavRoute) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onNavigate,
  mobileOpen,
  onCloseMobile,
}) => {
  const navItems: { route: NavRoute; label: string; icon: React.ReactNode }[] = [
    { route: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
    { route: "tutor", label: "AI Tutor", icon: <Bot size={18} /> },
    { route: "assessments", label: "Assessments", icon: <FileCheck2 size={18} /> },
    { route: "progress", label: "My Progress", icon: <TrendingUp size={18} /> },
    { route: "materials", label: "Course Materials", icon: <FolderGit2 size={18} /> },
    { route: "course-map", label: "Course Map", icon: <Network size={18} /> },
    { route: "settings", label: "Settings", icon: <Settings size={18} /> },
  ];

  const handleItemClick = (route: NavRoute) => {
    onNavigate(route);
    onCloseMobile();
  };

  return (
    <>
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}
      <aside
        className={`app-sidebar ${mobileOpen ? "open" : ""}`}
        aria-label="Sidebar Navigation"
      >
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.route}
              className={`sidebar-nav-item ${
                currentRoute === item.route ? "active" : ""
              }`}
              onClick={() => handleItemClick(item.route)}
              aria-current={currentRoute === item.route ? "page" : undefined}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p>AI Study Companion v1.0</p>
          <p style={{ marginTop: "4px" }}>Multimodal AI Hackathon 2026</p>
        </div>
      </aside>
    </>
  );
};
