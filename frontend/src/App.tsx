import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { DashboardView } from "./components/DashboardView";
import {
  TutorPage,
  AssessmentsPage,
  ProgressPage,
  MaterialsPage,
  CourseMapPage,
  SettingsPage,
} from "./pages/RoutePlaceholders";
import { initialDashboardData, newStudentDashboardData } from "./data/mockDashboardData";
import type { DashboardData, DashboardViewMode, NavRoute, CourseInfo } from "./types/dashboard";

export const App: React.FC = () => {
  // Navigation Route State (with hash sync)
  const [currentRoute, setCurrentRoute] = useState<NavRoute>("dashboard");
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  // Dashboard Data & State Modes
  const [dashboardData, setDashboardData] = useState<DashboardData>(initialDashboardData);
  const [viewMode, setViewMode] = useState<DashboardViewMode>("normal");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Sync route with URL hash for browser back/forward and direct bookmarks
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#/", "") as NavRoute;
      const validRoutes: NavRoute[] = [
        "dashboard",
        "tutor",
        "assessments",
        "progress",
        "materials",
        "course-map",
        "settings",
      ];
      if (validRoutes.includes(hash)) {
        setCurrentRoute(hash);
      } else {
        window.location.hash = "#/dashboard";
        setCurrentRoute("dashboard");
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const navigateTo = (route: NavRoute) => {
    window.location.hash = `#/${route}`;
    setCurrentRoute(route);
  };

  const showToast = (message: string) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 3200);
  };

  const handleSelectCourse = (course: CourseInfo) => {
    setDashboardData((prev) => ({
      ...prev,
      course,
    }));
    showToast(`Switched active course to ${course.name} (${course.code})`);
  };

  const handleSetViewMode = (mode: DashboardViewMode) => {
    setViewMode(mode);
    if (mode === "new_student") {
      setDashboardData(newStudentDashboardData);
    } else if (mode === "normal") {
      setDashboardData(initialDashboardData);
    }
    showToast(`Switched dashboard view state: ${mode.toUpperCase()}`);
  };

  const handleRetry = () => {
    setViewMode("loading");
    setTimeout(() => {
      setDashboardData(initialDashboardData);
      setViewMode("normal");
      showToast("Dashboard data reloaded successfully.");
    }, 800);
  };

  const handleStartDiagnostic = () => {
    showToast("Starting diagnostic assessment intake for new student...");
    setTimeout(() => {
      navigateTo("assessments");
    }, 600);
  };

  // Render appropriate view based on route
  const renderCurrentRouteView = () => {
    switch (currentRoute) {
      case "tutor":
        return <TutorPage onBack={() => navigateTo("dashboard")} />;
      case "assessments":
        return <AssessmentsPage onBack={() => navigateTo("dashboard")} />;
      case "progress":
        return <ProgressPage onBack={() => navigateTo("dashboard")} />;
      case "materials":
        return <MaterialsPage onBack={() => navigateTo("dashboard")} />;
      case "course-map":
        return <CourseMapPage onBack={() => navigateTo("dashboard")} />;
      case "settings":
        return <SettingsPage onBack={() => navigateTo("dashboard")} />;
      case "dashboard":
      default:
        return (
          <DashboardView
            data={dashboardData}
            viewMode={viewMode}
            onNavigateToRoute={navigateTo}
            onRetry={handleRetry}
            onStartDiagnostic={handleStartDiagnostic}
            onShowToast={showToast}
          />
        );
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        currentRoute={currentRoute}
        onNavigate={navigateTo}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Header
          currentCourse={dashboardData.course}
          availableCourses={dashboardData.availableCourses}
          onSelectCourse={handleSelectCourse}
          onToggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
          studentName={dashboardData.student.name}
          viewMode={viewMode}
          onSetViewMode={handleSetViewMode}
        />

        <main className="main-content" role="main">
          {renderCurrentRouteView()}
        </main>
      </div>

      {/* Toast Notification */}
      {toastMessage && (
        <aside className="toast-notice" role="status" aria-live="polite">
          {toastMessage}
        </aside>
      )}
    </div>
  );
};

export default App;
