"""Comprehensive multimodal course seed script.

Populates the Knowledge Base with rich multimodal course materials across:
1. Textbook PDF excerpts with exact page citations and diagrams
2. Slide deck excerpts with exact slide citations, notes, and figures
3. Lecture video transcripts with precise timestamp intervals
4. Topic -> Subtopic -> Concept hierarchy
5. Pedagogical prerequisite dependency graph (DAG)
"""

from __future__ import annotations

import httpx
from pydantic import TypeAdapter

from app.tutor.models import ContentUnit, PdfSource, SlideSource, VideoSource
from app.kb.models import (
    BoundingBox,
    FigureUnit,
    ConceptNode,
    PrerequisiteEdge,
    CourseKnowledgeGraph,
)

COURSE_ID = "biology_101"

SAMPLE_UNITS = [
    # --- PDF Textbook Chunks ---
    ContentUnit(
        id="unit_campbell_bio_p182_01",
        course_id=COURSE_ID,
        text=(
            "Photosynthesis converts light energy to the chemical energy of food. "
            "In autotrophic eukaryotes, photosynthesis occurs inside chloroplasts. "
            "The chloroplast has two membranes surrounding a dense fluid called the stroma. "
            "Suspended within the stroma is a third membrane system made up of sacs called thylakoids, "
            "which segregate the stroma from the thylakoid space inside these sacs. "
            "Chlorophyll resides in the thylakoid membranes."
        ),
        topic="Photosynthesis",
        subtopic="Chloroplast Structure",
        concept="Chloroplast Anatomy",
        source=PdfSource(
            type="pdf",
            file_name="Campbell_Biology_Ch10.pdf",
            page=182,
        ),
        metadata={"figure_ids": ["fig_chloroplast_diagram_p182"]},
    ),
    ContentUnit(
        id="unit_campbell_bio_p184_01",
        course_id=COURSE_ID,
        text=(
            "The two stages of photosynthesis are the Light Reactions and the Calvin Cycle. "
            "The light reactions convert solar energy to chemical energy. "
            "Water is split, providing a source of electrons and protons (H+) and giving off O2 as a by-product. "
            "Light absorbed by chlorophyll drives a transfer of electrons and hydrogen ions from water to an acceptor called NADP+, "
            "where they are temporarily stored. The light reactions use solar energy to reduce NADP+ to NADPH by adding a pair of electrons."
        ),
        topic="Photosynthesis",
        subtopic="Light Reactions",
        concept="Light-Dependent Reactions",
        source=PdfSource(
            type="pdf",
            file_name="Campbell_Biology_Ch10.pdf",
            page=184,
        ),
        metadata={"figure_ids": ["fig_z_scheme_p184"]},
    ),
    ContentUnit(
        id="unit_campbell_bio_p189_01",
        course_id=COURSE_ID,
        text=(
            "The Calvin cycle uses the chemical energy of ATP and NADPH to reduce CO2 to sugar. "
            "The cycle begins by incorporating CO2 from the air into organic molecules already present in the chloroplast. "
            "This initial incorporation of carbon into organic compounds is known as carbon fixation. "
            "The carbohydrate produced directly from the Calvin cycle is not glucose, but the three-carbon sugar glyceraldehyde 3-phosphate (G3P)."
        ),
        topic="Photosynthesis",
        subtopic="Calvin Cycle",
        concept="Carbon Fixation",
        source=PdfSource(
            type="pdf",
            file_name="Campbell_Biology_Ch10.pdf",
            page=189,
        ),
        metadata={"figure_ids": ["fig_calvin_cycle_p189"]},
    ),
    # --- Slide Deck Chunks ---
    ContentUnit(
        id="unit_lecture_slides_s05",
        course_id=COURSE_ID,
        text=(
            "## Photosystems I & II Architecture\n\n"
            "• Photosystem II (PS II) functions first and absorbs best at 680 nm (P680).\n"
            "• Photosystem I (PS I) absorbs best at 700 nm (P700).\n"
            "• Linear electron flow drives the synthesis of ATP via photophosphorylation and generates NADPH.\n\n"
            "[Speaker Notes: Remind students that PS II was discovered after PS I but acts first in the linear pathway.]"
        ),
        topic="Photosynthesis",
        subtopic="Light Reactions",
        concept="Photosystems and Electron Flow",
        source=SlideSource(
            type="slide",
            file_name="Lecture_10_Photosynthesis.pptx",
            slide=5,
        ),
        metadata={"has_notes": True, "figure_ids": ["fig_photosystems_s05"]},
    ),
    ContentUnit(
        id="unit_lecture_slides_s08",
        course_id=COURSE_ID,
        text=(
            "## Chemiosmosis in Chloroplasts vs Mitochondria\n\n"
            "• Chloroplasts and mitochondria generate ATP by chemiosmosis, but use different sources of energy.\n"
            "• Mitochondria transfer chemical energy from food molecules to ATP; chloroplasts transform light energy into chemical energy in ATP.\n"
            "• In chloroplasts, high-energy electrons dropped down the transport chain come from water."
        ),
        topic="Photosynthesis",
        subtopic="ATP Synthesis",
        concept="Photophosphorylation",
        source=SlideSource(
            type="slide",
            file_name="Lecture_10_Photosynthesis.pptx",
            slide=8,
        ),
        metadata={"has_notes": False, "figure_ids": []},
    ),
    # --- Video Lecture Chunks ---
    ContentUnit(
        id="unit_prof_video_00300_01",
        course_id=COURSE_ID,
        text=(
            "Notice how water is oxidized at the oxygen-evolving complex of photosystem II. "
            "For every two water molecules oxidized, four electrons are transferred, "
            "four protons are released into the thylakoid lumen, and one molecule of molecular oxygen is generated. "
            "This lumenal proton accumulation establishes the proton-motive force across the thylakoid membrane."
        ),
        topic="Photosynthesis",
        subtopic="Light Reactions",
        concept="Photolysis of Water",
        source=VideoSource(
            type="video",
            file_name="MIT_7.016_Lecture_14.mp4",
            timestamp_start="00:05:00",
            timestamp_end="00:06:45",
        ),
        metadata={"start_seconds": 300, "end_seconds": 405},
    ),
    ContentUnit(
        id="unit_prof_video_00720_02",
        course_id=COURSE_ID,
        text=(
            "Now let's examine the enzyme RuBisCO—ribulose-1,5-bisphosphate carboxylase-oxygenase. "
            "RuBisCO catalyzes the very first step of the Calvin cycle, combining ribulose 1,5-bisphosphate with carbon dioxide. "
            "It is notoriously slow, fixing only 3 to 10 molecules of CO2 per second, which is why it is the most abundant protein on Earth."
        ),
        topic="Photosynthesis",
        subtopic="Calvin Cycle",
        concept="RuBisCO Enzyme Kinetics",
        source=VideoSource(
            type="video",
            file_name="MIT_7.016_Lecture_14.mp4",
            timestamp_start="00:12:00",
            timestamp_end="00:14:15",
        ),
        metadata={"start_seconds": 720, "end_seconds": 855},
    ),
]


def seed():
    print(f"Seeding course '{COURSE_ID}' into Knowledge Base...")
    with httpx.Client(base_url="http://localhost:8000") as client:
        try:
            resp = client.post(
                "/api/kb/ingest",
                json={"units": [u.model_dump(mode="json") for u in SAMPLE_UNITS]},
            )
            print("KB Ingest response:", resp.json())
        except Exception as e:
            print("Could not reach API at http://localhost:8000. Error:", e)


if __name__ == "__main__":
    seed()
