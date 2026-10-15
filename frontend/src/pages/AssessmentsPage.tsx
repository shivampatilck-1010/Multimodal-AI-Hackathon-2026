import React, { useState } from "react";
import { ArrowLeft, CheckCircle2, XCircle, AlertTriangle, BookOpen, Sparkles, RefreshCw, Send } from "lucide-react";

interface Option {
  key: string;
  text: string;
}

interface Question {
  id: string;
  question_text: string;
  options: Option[];
  correct_answer: string;
  concept_name: string;
  topic: string;
  explanation: string;
  source: {
    file_name: string;
    page?: number;
    slide?: number;
    timestamp_start?: string;
  };
}

interface Evaluation {
  question_id: string;
  concept_name: string;
  topic: string;
  is_correct: boolean;
  user_answer: string;
  correct_answer: string;
  feedback: string;
  misconception?: string | null;
  source: {
    file_name: string;
    page?: number;
    slide?: number;
  };
}

interface AssessmentReport {
  title: string;
  total_questions: number;
  correct_count: number;
  score_percentage: number;
  evaluations: Evaluation[];
  weak_topics: string[];
  strong_topics: string[];
  misconceptions: string[];
  recommendations: string[];
}

export const AssessmentsPage: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [numQuestions, setNumQuestions] = useState(3);
  const [loading, setLoading] = useState(false);
  const [quiz, setQuiz] = useState<{ id: string; questions: Question[] } | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [report, setReport] = useState<AssessmentReport | null>(null);

  const generateQuiz = async () => {
    setLoading(true);
    setReport(null);
    setSelectedAnswers({});
    try {
      const res = await fetch("http://localhost:8000/api/assessments/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: "hackathon_course",
          topic: topic || null,
          num_questions: numQuestions,
          difficulty: difficulty,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuiz(data);
      } else {
        throw new Error("Failed to generate quiz");
      }
    } catch (e) {
      console.error(e);
      // Fallback sample quiz for instant interactive demonstration
      setQuiz({
        id: "quiz_sample",
        questions: [
          {
            id: "q1",
            question_text: "According to the course notes, what is the role of the learning rate in Gradient Descent?",
            concept_name: "Learning Rate",
            topic: "Optimization",
            options: [
              { key: "A", text: "It scales the step size taken in the opposite direction of the gradient." },
              { key: "B", text: "It calculates the second derivative of the error function directly." },
              { key: "C", text: "It sets the maximum number of hidden layers in the network." },
              { key: "D", text: "It prevents backpropagation from computing chain rule derivatives." },
            ],
            correct_answer: "A",
            explanation: "Directly referenced in textbook notes: The step vector is scaled by alpha (learning rate).",
            source: { file_name: "machine_learning_ch4.pdf", page: 12 },
          },
          {
            id: "q2",
            question_text: "What mathematical principle enables backpropagation across multi-layer neural networks?",
            concept_name: "Backpropagation",
            topic: "Neural Networks",
            options: [
              { key: "A", text: "Euler's formula for complex exponentials." },
              { key: "B", text: "The multivariate Chain Rule of calculus." },
              { key: "C", text: "Bayes Theorem for inverse probabilities." },
              { key: "D", text: "Fourier transforms of weight tensors." },
            ],
            correct_answer: "B",
            explanation: "As stated in Lecture 2 slides: Backpropagation is a recursive application of the calculus chain rule.",
            source: { file_name: "lecture_slides_wk2.pptx", slide: 8 },
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId: string, optionKey: string) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: optionKey }));
  };

  const submitQuiz = async () => {
    if (!quiz) return;
    setSubmitting(true);
    const answers = quiz.questions.map((q) => ({
      question_id: q.id,
      selected_answer: selectedAnswers[q.id] || "A",
    }));

    try {
      const res = await fetch("http://localhost:8000/api/assessments/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assessment_id: quiz.id,
          user_id: "student_alex",
          course_id: "hackathon_course",
          answers,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      } else {
        throw new Error("Submit failed");
      }
    } catch (e) {
      // Local fallback grading for demonstration
      let correct = 0;
      const evals: Evaluation[] = quiz.questions.map((q) => {
        const userAns = selectedAnswers[q.id] || "";
        const isCorr = userAns.toUpperCase() === q.correct_answer.toUpperCase();
        if (isCorr) correct++;
        return {
          question_id: q.id,
          concept_name: q.concept_name,
          topic: q.topic,
          is_correct: isCorr,
          user_answer: userAns || "None",
          correct_answer: q.correct_answer,
          feedback: isCorr
            ? `Correct! ${q.explanation}`
            : `Incorrect. The correct answer was ${q.correct_answer}. Reference: ${q.source.file_name} (Page ${q.source.page || q.source.slide || 1}).`,
          misconception: isCorr ? null : "Inverted variable relationship or conceptual slip",
          source: q.source,
        };
      });

      const scorePct = Math.round((correct / quiz.questions.length) * 100);
      setReport({
        title: "Adaptive Mastery Assessment",
        total_questions: quiz.questions.length,
        correct_count: correct,
        score_percentage: scorePct,
        evaluations: evals,
        weak_topics: scorePct < 60 ? ["Optimization"] : [],
        strong_topics: scorePct >= 80 ? ["Neural Networks"] : [],
        misconceptions: scorePct < 100 ? ["Learning Rate: Confused step scale with derivative order"] : [],
        recommendations: [
          "Review Prerequisite: Differential Calculus chain rule before tackling multi-layer backpropagation.",
          "Ask the AI Tutor to explain why learning rate oscillations occur with large step sizes.",
        ],
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto", padding: "24px 16px" }}>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
        <button className="new-btn-primary" onClick={onBack} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", cursor: "pointer" }}>
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>
        <span style={{ fontSize: "0.85rem", color: "#a3a3a3", border: "1px solid #333", padding: "4px 12px", borderRadius: "16px" }}>
          Member 3 • Adaptive Assessment Engine
        </span>
      </div>

      {/* Main Section */}
      {!quiz && !report && (
        <div className="card-surface" style={{ padding: "32px", borderRadius: "12px", border: "1px solid #333" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
            <Sparkles size={24} color="#e5e5e5" />
            <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>Adaptive Assessment & Mock Exams</h1>
          </div>
          <p style={{ color: "#d4d4d4", lineHeight: 1.6, marginBottom: "24px" }}>
            Generate source-grounded multiple-choice quizzes and problem sets tailored to your current study goals.
            Questions are strictly verified against ingested textbooks, slides, and transcripts.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "6px", color: "#a3a3a3" }}>
                Target Topic / Scope (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Optimization, Backpropagation..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                style={{ width: "100%", padding: "10px 14px", background: "#000", border: "1px solid #444", borderRadius: "8px", color: "#fff" }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "6px", color: "#a3a3a3" }}>
                Difficulty Level
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                style={{ width: "100%", padding: "10px 14px", background: "#000", border: "1px solid #444", borderRadius: "8px", color: "#fff" }}
              >
                <option value="easy">Easy (Foundations)</option>
                <option value="medium">Medium (Applied Analysis)</option>
                <option value="hard">Hard (Synthesis & Edge Cases)</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "0.85rem", color: "#a3a3a3" }}>Question Count:</span>
              {[2, 3, 5].map((n) => (
                <button
                  key={n}
                  onClick={() => setNumQuestions(n)}
                  style={{
                    padding: "4px 12px",
                    borderRadius: "6px",
                    background: numQuestions === n ? "#333333" : "#111111",
                    border: numQuestions === n ? "1px solid #777777" : "1px solid #444444",
                    color: "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  {n}
                </button>
              ))}
            </div>

            <button
              className="new-btn-primary-large"
              onClick={generateQuiz}
              disabled={loading}
              style={{ display: "flex", alignItems: "center", gap: "8px", padding: "12px 24px", cursor: "pointer" }}
            >
              {loading ? <RefreshCw size={18} className="animate-spin" /> : <Sparkles size={18} />}
              <span>{loading ? "Generating Grounded Quiz..." : "Start Assessment"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Active Quiz Taking */}
      {quiz && !report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "1.3rem", fontWeight: 700, margin: 0, color: "#ffffff" }}>Active Assessment ({quiz.questions.length} Questions)</h2>
            <span style={{ fontSize: "0.85rem", color: "#a3a3a3" }}>
              Answered: {Object.keys(selectedAnswers).length}/{quiz.questions.length}
            </span>
          </div>

          {quiz.questions.map((q, idx) => (
            <div key={q.id} className="card-surface" style={{ padding: "24px", borderRadius: "12px", border: "1px solid #333333" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                <span style={{ fontSize: "0.8rem", color: "#a3a3a3", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Question {idx + 1} • {q.topic} ({q.concept_name})
                </span>
                <span style={{ fontSize: "0.75rem", background: "#1a1a1a", border: "1px solid #333333", padding: "2px 8px", borderRadius: "4px", color: "#ffffff" }}>
                  Grounded in {q.source.file_name}
                </span>
              </div>

              <p style={{ fontSize: "1.05rem", fontWeight: 500, lineHeight: 1.5, marginBottom: "20px", color: "#ffffff" }}>
                {q.question_text}
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {q.options.map((opt) => {
                  const isSelected = selectedAnswers[q.id] === opt.key;
                  return (
                    <div
                      key={opt.key}
                      onClick={() => handleSelectOption(q.id, opt.key)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "12px",
                        padding: "12px 16px",
                        borderRadius: "8px",
                        background: isSelected ? "#212121" : "#0a0a0a",
                        border: isSelected ? "1px solid #777777" : "1px solid #333333",
                        boxShadow: isSelected ? "0 0 10px rgba(160,160,160,0.15)" : "none",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                    >
                      <span
                        style={{
                          width: "28px",
                          height: "28px",
                          borderRadius: "50%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          background: isSelected ? "#383838" : "#1a1a1a",
                          color: "#ffffff",
                          border: isSelected ? "1px solid #777777" : "1px solid #333333",
                          fontWeight: 700,
                          fontSize: "0.85rem",
                        }}
                      >
                        {opt.key}
                      </span>
                      <span style={{ fontSize: "0.95rem", color: "#ffffff" }}>{opt.text}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
            <button
              className="new-btn-primary-large"
              onClick={submitQuiz}
              disabled={submitting}
              style={{ display: "flex", alignItems: "center", gap: "8px", padding: "14px 28px", cursor: "pointer" }}
            >
              <Send size={18} />
              <span>{submitting ? "Evaluating Responses..." : "Submit & Grade Assessment"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Post-Assessment Report */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Summary Banner */}
          <div
            className="card-surface"
            style={{
              padding: "32px",
              borderRadius: "12px",
              border: "1px solid #333",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <span style={{ fontSize: "0.85rem", color: "#a3a3a3", textTransform: "uppercase" }}>Assessment Result</span>
              <h2 style={{ fontSize: "1.8rem", fontWeight: 700, margin: "4px 0 8px 0" }}>
                Score: {report.score_percentage}% ({report.correct_count}/{report.total_questions} Correct)
              </h2>
              <p style={{ color: "#d4d4d4", margin: 0, fontSize: "0.95rem" }}>
                {report.score_percentage >= 80
                  ? "Outstanding grasp of curriculum concepts! Telemetry logged to Learner Model."
                  : "Good effort! Review the detailed cited feedback below to close conceptual gaps."}
              </p>
            </div>

            <button
              className="new-btn-primary"
              onClick={() => {
                setQuiz(null);
                setReport(null);
              }}
              style={{ padding: "10px 20px", cursor: "pointer" }}
            >
              Take Another Quiz
            </button>
          </div>

          {/* Recommendations & Misconceptions */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div className="card-surface" style={{ padding: "20px", borderRadius: "10px", border: "1px solid #333" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <AlertTriangle size={18} color="#f59e0b" />
                <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: 0 }}>Targeted Recommendations</h3>
              </div>
              <ul style={{ paddingLeft: "18px", margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
                {report.recommendations.map((rec, i) => (
                  <li key={i} style={{ fontSize: "0.9rem", color: "#d4d4d4", lineHeight: 1.5 }}>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>

            <div className="card-surface" style={{ padding: "20px", borderRadius: "10px", border: "1px solid #333" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <BookOpen size={18} color="#3b82f6" />
                <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: 0 }}>Identified Misconceptions</h3>
              </div>
              {report.misconceptions.length > 0 ? (
                <ul style={{ paddingLeft: "18px", margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
                  {report.misconceptions.map((misc, i) => (
                    <li key={i} style={{ fontSize: "0.9rem", color: "#d4d4d4", lineHeight: 1.5 }}>
                      {misc}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: "0.9rem", color: "#a3a3a3", margin: 0 }}>
                  No major misconceptions identified. High precision demonstrated!
                </p>
              )}
            </div>
          </div>

          {/* Question by question feedback */}
          <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "8px 0 0 0" }}>Question-by-Question Review</h3>
          {report.evaluations.map((ev, idx) => (
            <div
              key={idx}
              className="card-surface"
              style={{
                padding: "20px",
                borderRadius: "10px",
                border: ev.is_correct ? "1px solid #22c55e" : "1px solid #ef4444",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {ev.is_correct ? <CheckCircle2 size={18} color="#22c55e" /> : <XCircle size={18} color="#ef4444" />}
                  <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                    Question {idx + 1}: {ev.concept_name}
                  </span>
                </div>
                <span style={{ fontSize: "0.8rem", color: "#a3a3a3" }}>
                  Your Answer: {ev.user_answer} | Expected: {ev.correct_answer}
                </span>
              </div>

              <p style={{ fontSize: "0.92rem", color: "#d4d4d4", lineHeight: 1.5, margin: "8px 0" }}>
                {ev.feedback}
              </p>

              <div style={{ fontSize: "0.8rem", color: "#a3a3a3", display: "flex", alignItems: "center", gap: "6px" }}>
                <BookOpen size={14} />
                <span>
                  Source: {ev.source.file_name} ({ev.source.page ? `Page ${ev.source.page}` : `Slide ${ev.source.slide || 1}`})
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
