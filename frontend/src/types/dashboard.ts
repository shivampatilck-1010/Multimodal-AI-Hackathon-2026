/**
 * Frontend-only types for the Student Dashboard.
 * These interfaces model the visual state and contracts for the UI.
 */

export type MasteryLevel = "strong" | "developing" | "needs_attention";

export interface StudentInfo {
  id: string;
  name: string;
  avatarUrl?: string;
  isNewStudent?: boolean;
}

export interface CourseInfo {
  id: string;
  name: string;
  code: string;
  instructor?: string;
}

export interface SummaryMetric {
  id: string;
  title: string;
  value: string;
  subtitle: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  iconName: string;
}

export interface ConceptItem {
  id: string;
  name: string;
  status: "mastered" | "developing" | "needs_work";
}

export interface SourceCitation {
  type: "textbook" | "slide" | "video";
  label: string;
  location: string;
  linkPreview?: string;
}

export interface TopicData {
  id: string;
  name: string;
  masteryPercentage: number;
  status: MasteryLevel;
  concepts: ConceptItem[];
  sources: SourceCitation[];
}

export interface PriorityTopicData {
  topicName: string;
  masteryPercentage: number;
  focusConcept: string;
  message: string;
  topicId: string;
}

export interface RecommendationData {
  id: string;
  title: string;
  actionName: string;
  reason: string;
  topicId: string;
  conceptName: string;
}

export interface AssessmentSummary {
  id: string;
  title: string;
  topicName: string;
  score: number;
  totalQuestions: number;
  correctCount: number;
  incorrectCount: number;
  strongAreas: string[];
  weakAreas: string[];
  completedAt: string;
}

export interface ContinueLearningData {
  courseName: string;
  currentTopic: string;
  lastActivity: string;
  progressPercentage: number;
}

export interface MaterialItem {
  id: string;
  type: "pdf" | "pptx" | "video";
  title: string;
  formatLabel: string;
  detail: string; // e.g. "428 pages", "32 slides", "12 lectures"
}

export interface ActivityDay {
  day: string; // "Mon", "Tue", ...
  hours: number;
  dateStr: string;
}

export interface MasteryHistoryPoint {
  period: string; // "W1", "W2", ...
  mastery: number; // 0 - 100
  label?: string;
}

export interface DashboardData {
  student: StudentInfo;
  course: CourseInfo;
  availableCourses: CourseInfo[];
  summary: SummaryMetric[];
  topics: TopicData[];
  priorityTopic: PriorityTopicData;
  recommendation: RecommendationData;
  assessment: AssessmentSummary;
  continueLearning: ContinueLearningData;
  materials: MaterialItem[];
  activity: ActivityDay[];
  masteryHistory: MasteryHistoryPoint[];
}

export type DashboardViewMode = "normal" | "new_student" | "loading" | "empty" | "error";

export type NavRoute =
  | "dashboard"
  | "tutor"
  | "assessments"
  | "progress"
  | "materials"
  | "course-map"
  | "settings";
