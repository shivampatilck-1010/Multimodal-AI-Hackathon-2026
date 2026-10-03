import { Search, Menu, Sparkles } from "lucide-react";
import type { CourseInfo, DashboardViewMode } from "../types/dashboard";

interface HeaderProps {
  currentCourse: CourseInfo;
  availableCourses: CourseInfo[];
  onSelectCourse: (course: CourseInfo) => void;
  onToggleMobileMenu: () => void;
  studentName: string;
  viewMode: DashboardViewMode;
  onSetViewMode: (mode: DashboardViewMode) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentCourse,
  availableCourses,
  onSelectCourse,
  onToggleMobileMenu,
  studentName,
  viewMode,
  onSetViewMode,
}) => {
  return (
    <header className="app-header" role="banner">
      <div className="header-left">
        <button
          className="mobile-menu-btn"
          onClick={onToggleMobileMenu}
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} />
        </button>

        <a href="#/dashboard" className="logo-area" aria-label="LearnAI Home">
          <div className="logo-icon" aria-hidden="true">
            <Sparkles size={18} />
          </div>
          <span>LearnAI</span>
        </a>

        <div className="course-selector-wrapper">
          <label htmlFor="course-dropdown" className="sr-only">
            Select Course
          </label>
          <select
            id="course-dropdown"
            className="course-selector"
            value={currentCourse.id}
            onChange={(e) => {
              const selected = availableCourses.find((c) => c.id === e.target.value);
              if (selected) onSelectCourse(selected);
            }}
          >
            {availableCourses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="header-center">
        <div className="search-box">
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            className="search-input"
            placeholder="Search concepts, lectures, slides..."
            aria-label="Search course content"
          />
        </div>
      </div>

      <div className="header-right">
        {/* Interactive View State Switcher to easily test all 5 dashboard states */}
        <div className="state-switcher" role="group" aria-label="Test Dashboard States">
          <button
            className={`state-switcher-btn ${viewMode === "normal" ? "active" : ""}`}
            onClick={() => onSetViewMode("normal")}
            title="Standard student dashboard view"
          >
            Normal
          </button>
          <button
            className={`state-switcher-btn ${viewMode === "new_student" ? "active" : ""}`}
            onClick={() => onSetViewMode("new_student")}
            title="State for a new student with no history"
          >
            New Student
          </button>
          <button
            className={`state-switcher-btn ${viewMode === "loading" ? "active" : ""}`}
            onClick={() => onSetViewMode("loading")}
            title="Skeleton loading state"
          >
            Loading
          </button>
          <button
            className={`state-switcher-btn ${viewMode === "empty" ? "active" : ""}`}
            onClick={() => onSetViewMode("empty")}
            title="Empty course state"
          >
            Empty
          </button>
          <button
            className={`state-switcher-btn ${viewMode === "error" ? "active" : ""}`}
            onClick={() => onSetViewMode("error")}
            title="Error state with retry"
          >
            Error
          </button>
        </div>

        <button className="user-profile" aria-label={`Signed in as ${studentName}`}>
          <div className="user-avatar" aria-hidden="true">
            {studentName.charAt(0)}
          </div>
          <span className="user-name">{studentName}</span>
        </button>
      </div>
    </header>
  );
};
