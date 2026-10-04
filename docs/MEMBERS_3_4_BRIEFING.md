# Phase 2 Briefing: Assessments & Learner Modeling

**To:** Member 3 (Assessment Engineer) & Member 4 (Learner Model Engineer)  
**From:** Core Infrastructure Team (Members 1 & 2)  
**Status:** Project Phase 1 Complete (Ingestion, RAG, & Frontend Scaffolding)  

---

## 🎯 The Current State of the Project

We have successfully completed the foundational layer of the application. The system can now ingest multimodal data and answer student questions safely.

**What is already built and working:**
*   **Multimodal Ingestion (Member 1):** We can automatically parse PDFs, PowerPoints, and Videos. The system extracts text, diagram bounding boxes, and organizes everything into a hierarchical "Prerequisite Graph" of concepts.
*   **Source-Grounded AI Tutor (Member 2):** We have a highly secure, hallucination-free generative AI Tutor. It strictly retrieves chunks from the knowledge base and cites its sources. 
*   **Frontend Dashboard (Member 1):** A React/Vite frontend is live, containing placeholders for the learning paths, assessments, and mastery metrics.

---

## ⚠️ Why Your Work is Critical (The "So What?")

Track D of the Hackathon is **"Personalized Tutoring & Adaptive Learning"**. 
Right now, we have a fancy search engine and a chat bot. **We do not yet have a personalized learning system.** 

To win this track, the system must *adapt* to the student. It needs to test them, find their weaknesses, and change the curriculum to help them improve. That entire adaptive loop relies completely on the two of you.

---

## 📝 Member 3: Assessment Engineer

Your mission is to prove whether the student actually learned the material. You will use the AI to generate dynamic, course-grounded quizzes.

**Your Action Items:**
1.  **Generate Grounded MCQs:** Write a service that takes a `concept_id` (e.g., "Photosynthesis") and asks the Member 2 `Retriever` for the exact course text about it. Use the LLM to generate a Multiple Choice Question strictly based on that text.
2.  **Evaluate Answers:** Build an endpoint that receives the student's answer, grades it (Correct/Incorrect), and uses the course material to explain *why* the answer was right or wrong.
3.  **Prevent Hallucination:** Ensure your generated questions do not ask things that aren't in the uploaded course material.
4.  **Connect to the UI:** Hook your generation and evaluation endpoints into the Assessment UI components on the React frontend.

**Your Key Interfaces:**
*   You will call Member 1's `/api/kb/courses/{course_id}/concepts` to figure out what to quiz the student on.
*   You will call Member 2's `Retriever.retrieve()` to get the raw text needed to generate the question.

---

## 🧠 Member 4: Learner Model Engineer

Your mission is to build the "brain" that remembers the student. You are responsible for the personalization aspect of the hackathon.

**Your Action Items:**
1.  **Mastery Database:** Design a database schema that records a student's proficiency (e.g., 0 to 100%) for every single concept in the course.
2.  **Consume Telemetry:** Listen to events from the rest of the system to update the student's score. 
    *   *When Member 3 grades a quiz:* Increase or decrease the mastery score for that concept.
    *   *When Member 2 answers a tutor question:* Log that the student is struggling with or exploring that concept.
3.  **Adaptive Routing:** Use Member 1's Prerequisite DAG (Directed Acyclic Graph). If a student fails a quiz on "Cellular Respiration", your system should look at the graph, realize they don't understand the prerequisite ("ATP"), and recommend they review ATP next.
4.  **Populate the Dashboard:** Serve the data that lights up the "Mastery Trend", "Priority Topic", and "Recommendation" cards on the frontend dashboard.

**Your Key Interfaces:**
*   You will consume the `TutorTurnEvent` emitted by Member 2.
*   You will consume the grading results output by Member 3.
*   You will query Member 1's `/api/kb/courses/{course_id}/prerequisites` to make adaptive recommendations.

---

## 🚀 Next Steps
We recommend Member 3 starts immediately on the **MCQ Generation Endpoint**, while Member 4 designs the **Student Mastery Database Schema**. Let's get building!
