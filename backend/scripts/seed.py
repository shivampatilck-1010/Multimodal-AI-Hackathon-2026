"""Seed script to populate a mock course."""

import json
import httpx
from pydantic import TypeAdapter
from typing import List

from app.tutor.models import ContentUnit, PdfSource, VideoSource

mock_course = [
    {
        "id": "pdf-1",
        "course_id": "hackathon_course",
        "text": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.",
        "source": {
            "type": "pdf",
            "file_name": "Biology 101.pdf",
            "page": 42
        },
        "topic": "Photosynthesis",
        "concept": "Process Overview"
    },
    {
        "id": "video-1",
        "course_id": "hackathon_course",
        "text": "The Krebs cycle, also known as the citric acid cycle, is a series of chemical reactions used by all aerobic organisms to release stored energy.",
        "source": {
            "type": "video",
            "file_name": "Cellular Respiration Lecture.mp4",
            "timestamp_start": "06:00"
        },
        "topic": "Krebs Cycle",
        "concept": "Energy Release"
    }
]

def run():
    print("Seeding database...")
    adapter = TypeAdapter(List[ContentUnit])
    units = adapter.validate_python(mock_course)
    
    with httpx.Client() as client:
        # Assuming app is running on localhost:8000
        try:
            resp = client.post(
                "http://localhost:8000/api/kb/ingest", 
                json={"units": [u.model_dump() for u in units]}
            )
            print("Response:", resp.json())
        except Exception as e:
            print("Could not connect to the API. Make sure it is running on http://localhost:8000.")
            print("Error:", e)

if __name__ == "__main__":
    run()
