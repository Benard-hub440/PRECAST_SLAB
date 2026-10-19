"""Local vision-model drawing interpretation and safe conversion to takeoffs."""
import base64
import json

import httpx

try:
    import fitz  # PyMuPDF
except ImportError:  # Keep the ordinary estimator usable until dependencies are installed.
    fitz = None

from app.core.config import OLLAMA_URL, OLLAMA_VISION_MODEL
from app.schemas.drawing import DrawingAnalysisResponse, DrawingRoom, DrawingRoomTakeoff
from app.schemas.estimate import EstimateInput
from app.services.calculator import calculate_estimate

MAX_PDF_PAGES = 8

PROMPT = """You are reading an architectural or structural slab drawing PDF. Extract ONLY enclosed
slab/room areas whose two dimensions are explicitly dimensioned or unambiguously labelled.
Interpret dimensions in metres; convert mm to metres. Do not infer dimensions from drawing scale.
Ignore columns, notes, reinforcement marks and elevations. Return valid JSON only, with this exact
shape: {\"drawing_notes\":[\"...\"],\"rooms\":[{\"name\":\"...\",\"length_m\":5.0,\"width_m\":4.0,\"confidence\":0.0,\"evidence\":\"dimension labels used\"}]}. If no safely measurable rooms exist, return an empty rooms list.\n"""


class DrawingReadError(Exception):
    pass


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _render_pdf_pages(pdf_bytes: bytes) -> list[str]:
    """Render drawing sheets in memory; no uploaded drawing is written to disk."""
    if fitz is None:
        raise DrawingReadError("PDF support is not installed. Run: pip install -r requirements.txt")
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        if document.page_count == 0:
            raise ValueError("empty PDF")
        pages = []
        for index in range(min(document.page_count, MAX_PDF_PAGES)):
            page = document.load_page(index)
            # 144 DPI retains ordinary dimension text while constraining model input size.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False)
            pages.append(base64.b64encode(pixmap.tobytes("png")).decode("ascii"))
        document.close()
        return pages
    except (RuntimeError, ValueError) as exc:
        raise DrawingReadError("The uploaded file is not a readable PDF drawing.") from exc


async def analyse_drawing(pdf_bytes: bytes, filename: str) -> DrawingAnalysisResponse:
    encoded_pages = _render_pdf_pages(pdf_bytes)
    payload = {
        "model": OLLAMA_VISION_MODEL,
        "stream": False,
        "format": "json",
        "messages": [{"role": "user", "content": PROMPT + f"File: {filename}. Read all supplied sheets as one drawing set.", "images": encoded_pages}],
        "options": {"temperature": 0},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{OLLAMA_URL.rstrip('/')}/api/chat", json=payload)
            response.raise_for_status()
            content = response.json()["message"]["content"]
    except (httpx.HTTPError, KeyError, TypeError) as exc:
        raise DrawingReadError(
            f"Local vision model is unavailable. Start Ollama and pull '{OLLAMA_VISION_MODEL}', then retry."
        ) from exc
    try:
        raw = json.loads(_strip_code_fence(content))
        rooms = [DrawingRoom.model_validate(item) for item in raw.get("rooms", [])]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise DrawingReadError("The local model did not return usable room measurements. Try a clearer exported drawing.") from exc

    takeoffs = []
    for room in rooms:
        estimate = calculate_estimate(EstimateInput(length_m=room.length_m, width_m=room.width_m, room_name=room.name, save=False))
        takeoffs.append(DrawingRoomTakeoff(room=room, estimate=estimate))
    return DrawingAnalysisResponse(
        model=OLLAMA_VISION_MODEL,
        drawing_notes=[str(note) for note in raw.get("drawing_notes", [])][:20],
        rooms=takeoffs,
        total_panels_to_order=sum(item.estimate.panels_to_order for item in takeoffs),
        total_wall_panels_to_order=sum(item.estimate.wall_panels_to_order for item in takeoffs),
        total_t_beams=sum(item.estimate.beam_count for item in takeoffs),
        total_beam_linear_meters=round(sum(item.estimate.total_beam_linear_meters for item in takeoffs), 2),
    )
