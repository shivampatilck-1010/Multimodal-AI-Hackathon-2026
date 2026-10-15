
const API_BASE_URL = "http://127.0.0.1:8080";

export interface BackendConcept {
  id: string;
  course_id: string;
  name: string;
  topic: string;
  subtopic?: string | null;
  summary?: string;
  content_unit_ids: string[];
  figure_ids: string[];
  metadata?: Record<string, unknown>;
}

export interface EvidenceUnit {
  id: string;
  course_id: string;
  text: string;
  topic?: string | null;
  subtopic?: string | null;
  concept?: string | null;
  source: {
    file_name: string;
    type: string;
    page?: number | null;
    slide?: number | null;
    timestamp_start?: string | null;
    timestamp_end?: string | null;
    start_seconds?: number | null;
    end_seconds?: number | null;
  };
  metadata?: Record<string, unknown>;
}

export interface EvidenceFigure {
  id?: string;
  caption?: string;
  explanation?: string;
  associated_concepts?: string[];
}

export interface ConceptEvidence {
  concept: BackendConcept;
  units: EvidenceUnit[];
  figures: EvidenceFigure[];
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;

    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // Keep the HTTP status when the response isn't JSON.
    }

    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function getCourseConcepts(
  courseId: string,
): Promise<BackendConcept[]> {
  const url =
    `${API_BASE_URL}/api/kb/courses/` +
    `${encodeURIComponent(courseId)}/concepts`;

  return parseResponse<BackendConcept[]>(await fetch(url));
}

export async function getConceptEvidence(
  courseId: string,
  conceptId: string,
): Promise<ConceptEvidence> {
  const url =
    `${API_BASE_URL}/api/kb/courses/` +
    `${encodeURIComponent(courseId)}/concepts/` +
    `${encodeURIComponent(conceptId)}/evidence`;

  return parseResponse<ConceptEvidence>(await fetch(url));
}

export interface TutorCitation {
  label: string;
  source_id: string;
  course_id: string;
  source_type: string;
  file_name: string;
  page?: number | null;
  slide?: number | null;
  timestamp_start?: string | null;
  timestamp_end?: string | null;
  start_seconds?: number | null;
  location?: string | null;
  link?: string | null;
  topic?: string | null;
  concept?: string | null;
  excerpt?: string | null;
}

export interface TutorResponse {
  answer: string;
  grounded: boolean;
  citations: TutorCitation[];
  evidence_ids: string[];
  unsupported_reason?: string | null;
  outside_knowledge?: string | null;
  related_topics: string[];
}

export async function askTutor(
  query: string,
  courseId = "cs229",
  sessionId = "demo-session",
  level = "intermediate"
): Promise<TutorResponse> {
  const response = await fetch(`${API_BASE_URL}/api/tutor/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      query,
      level,
      course_id: courseId,
    }),
  });

  return parseResponse<TutorResponse>(response);
}
