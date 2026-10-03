# Student Dashboard — Frontend Documentation

## 1. Overview

The Student Dashboard is a modern, educational SaaS interface designed for an AI study companion. It provides an immediate, unified view of a student's curriculum mastery, recent assessment performance, recommended actions, study activity, and multimodal course materials.

This is a **frontend-only** implementation that strictly uses structured mock data and client-side state, allowing seamless independent testing before backend APIs are connected.

---

## 2. Dashboard Structure & Layout

The dashboard follows a standard desktop and mobile-responsive layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [LearnAI Logo]   [Course Dropdown ▼]   [🔍 Search]   [👤 Alex Morgan]  │
├─────────────────┬──────────────────────────────────────────────────────┤
│ ❖ Dashboard     │ Good morning, Alex 👋                                │
│ ❖ AI Tutor      │ Here's where you should focus today.                 │
│ ❖ Assessments   ├──────────────────────────────────────────────────────┤
│ ❖ My Progress   │ [OVERALL MASTERY] [PROGRESS] [QUESTIONS] [ACTIVITY]  │
│ ❖ Materials     ├──────────────────────────┬───────────────────────────┤
│ ❖ Course Map    │ TOPIC MASTERY            │ ⚠ Priority Topic          │
│ ❖ Settings      │  • Neural Networks (82%) │ 🎯 Recommended Next       │
│                 │  • Backprop (72%)        │ 📊 Latest Assessment      │
│                 │  • Regression (61%)      │ ▶ Continue Learning       │
│                 │  • Optimization (43%)    │ 💬 Ask Tutor Quick Action │
│                 │  • Linear Algebra (37%)  │ 📁 Course Materials       │
│                 │ ──────────────────────── │                           │
│                 │ LEARNING ACTIVITY (Bars) │                           │
│                 │ MASTERY TREND (SVG Line) │                           │
└─────────────────┴──────────────────────────┴───────────────────────────┘
```

---

## 3. Component Architecture

All components reside in `frontend/src/components/`:

| Component | File | Description |
| :--- | :--- | :--- |
| **Header** | `Header.tsx` | App logo, course switcher dropdown, search input, test state switcher pills, student avatar. |
| **Sidebar** | `Sidebar.tsx` | Primary navigation drawer (Dashboard, Tutor, Assessments, Progress, Materials, Course Map, Settings). Mobile-responsive overlay. |
| **SummaryCards** | `SummaryCards.tsx` | Reusable summary metric cards (Overall Mastery: 68%, Progress: +7%, Questions: 47, Study Activity: 4.2 hrs). |
| **TopicMastery** | `TopicMastery.tsx` | Interactive topic progress cards with distinct visual badges (`strong`, `developing`, `needs_attention`). Clicking opens the detail modal. |
| **TopicDetailModal** | `TopicDetailModal.tsx` | Accessible modal dialog (ESC to close) showing topic concepts breakdown and cited multimodal sources (Textbook, Slides, Lecture Video). |
| **PriorityTopic** | `PriorityTopic.tsx` | Prominent alert card emphasizing topics needing immediate remediation (Optimization 43%). |
| **RecommendationCard** | `RecommendationCard.tsx` | Pedagogical next steps ("Review Learning Rate") with [Review], [Practice], and [Ask Tutor] buttons. |
| **RecentAssessment** | `RecentAssessment.tsx` | Results from latest assessment (7/10), breakdown of correct/incorrect questions, strengths, and weak areas. |
| **ContinueLearning** | `ContinueLearning.tsx` | Resume last study session (Machine Learning — Backpropagation). |
| **TutorQuickAction** | `TutorQuickAction.tsx` | One-click prompt suggestion entry into the AI Tutor interface. |
| **LearningActivity** | `LearningActivity.tsx` | 7-day study hours bar visualization with hover tooltips and daily metrics. |
| **MasteryTrend** | `MasteryTrend.tsx` | Responsive SVG line chart mapping weekly progress (W1 through W5) with hover milestones. |
| **CourseMaterials** | `CourseMaterials.tsx` | Overview of multimodal course assets (Textbook PDF, Lecture Slides PPTX, Video Lectures MP4). |
| **SkeletonLoader** | `SkeletonLoader.tsx` | Polished shimmer skeleton loading state. |
| **EmptyState** | `EmptyState.tsx` | Empty course placeholder with CTA to upload or start learning. |
| **ErrorState** | `ErrorState.tsx` | Resilient error recovery screen with a [Retry] button that reloads mock data. |
| **NewStudentState** | `NewStudentState.tsx` | Welcome state for newly enrolled students with a [Start Diagnostic] CTA. |

---

## 4. Routes & Navigation Targets

The application supports clean client-side routing synchronized with `window.location.hash`:

- `#/dashboard` — Main student dashboard (Active default).
- `#/tutor` — AI Tutor conversational interface (Placeholder owned by Member 2).
- `#/assessments` — Adaptive assessment generation & exams (Placeholder owned by Member 3).
- `#/progress` — Longitudinal student mastery tracking (Placeholder owned by Member 4).
- `#/materials` — Multimodal knowledge base viewer (Placeholder owned by Member 1).
- `#/course-map` — Curriculum prerequisite DAG visualization (Placeholder owned by Member 1).
- `#/settings` — Student settings & difficulty preference.

All non-dashboard routes display dedicated, non-broken placeholder screens with back-navigation buttons.

---

## 5. Mock Data Model

All data is decoupled from UI components and stored in `frontend/src/data/mockDashboardData.ts`:

- `student`: Name, avatar, enrollment status.
- `course` & `availableCourses`: Active course and switcher list.
- `summary`: Metric cards values, subtitles, and positive/negative trends.
- `topics`: 5 core modules with percentage, mastery levels, concepts checklist, and source citations.
- `priorityTopic`: Topic needing immediate remediation with rationale.
- `recommendation`: Actionable next concept recommendation.
- `assessment`: Latest score (7/10), correct/incorrect counts, strengths, weaknesses.
- `continueLearning`: Current module in progress with percentage.
- `materials`: Multimodal asset catalog with page/slide/video counts.
- `activity`: Daily study hours array (Mon through Sun).
- `masteryHistory`: Weekly progress milestones (W1 to W5).

---

## 6. Testing Dashboard States

A state switcher toolbar is embedded in the top header to facilitate instantaneous testing of all 5 UI states:

1. **Normal**: Standard view with all metrics, topics, charts, and recommendations populated.
2. **New Student**: Welcome intake screen with diagnostic call-to-action.
3. **Loading**: Pulse-shimmer skeleton layout for all card grids and charts.
4. **Empty**: Empty course state prompting for course materials.
5. **Error**: Network/retrieval failure screen with working [Retry] button.

---

## 7. Responsive Behavior

- **Desktop (>1024px)**: Fixed left sidebar (250px), 4-column summary metric grid, 2-column main dashboard (2:1 ratio).
- **Tablet (768px - 1024px)**: 2-column summary metrics, single-column stacked layout.
- **Mobile (<768px)**: Hidden sidebar accessible via hamburger button drawer overlay, single-column stacked cards, full-width touch-friendly buttons, horizontally contained SVG charts without overflow.

---

## 8. How to Run the Frontend

### Prerequisites
- Node.js 18+ (tested on Node v24.14.0)
- npm 9+

### Commands

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```powershell
   npm install
   ```

3. Start development dev server:
   ```powershell
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

4. Build production bundle (TypeScript & Vite validation):
   ```powershell
   npm run build
   ```
