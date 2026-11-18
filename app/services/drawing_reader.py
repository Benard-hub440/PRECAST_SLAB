"""Vision-model drawing interpretation and safe conversion to takeoffs."""
import base64
import json

import httpx

try:
    import fitz  # PyMuPDF
except ImportError:  # Keep the ordinary estimator usable until dependencies are installed.
    fitz = None

from app.core.config import VISION_API_KEY, VISION_API_URL, VISION_MODEL, VISION_PROVIDER
from app.schemas.drawing import DrawingAnalysisResponse, DrawingRoom, DrawingRoomTakeoff
from app.schemas.estimate import EstimateInput
from app.services.calculator import calculate_estimate

MAX_PDF_PAGES = 8
MAX_RENDERED_PAGE_PIXELS = 20_000_000

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
            if page.rect.width * page.rect.height * 4 > MAX_RENDERED_PAGE_PIXELS:
                raise DrawingReadError("A drawing page is too large to process safely. Export it at a smaller page size.")
            # 144 DPI retains ordinary dimension text while constraining model input size.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False)
            pages.append(base64.b64encode(pixmap.tobytes("png")).decode("ascii"))
        document.close()
        return pages
    except (RuntimeError, ValueError) as exc:
        raise DrawingReadError("The uploaded file is not a readable PDF drawing.") from exc


async def _read_with_vision_model(encoded_pages: list[str], filename: str) -> str:
    if not VISION_MODEL:
        raise DrawingReadError("Set VISION_MODEL to a multimodal model in .env before analysing drawings.")
    prompt = PROMPT + f"File: {filename}. Read all supplied sheets as one drawing set."
    if VISION_PROVIDER == "ollama":
        url = f"{VISION_API_URL.rstrip('/')}/api/chat"
        payload = {
            "model": VISION_MODEL,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt, "images": encoded_pages}],
            "options": {"temperature": 0},
        }
    elif VISION_PROVIDER == "openai_compatible":
        url = VISION_API_URL
        payload = {
            "model": VISION_MODEL,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": prompt}] + [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{page}"}}
                    for page in encoded_pages
                ],
            }],
        }
    else:
        raise DrawingReadError("VISION_PROVIDER must be 'ollama' or 'openai_compatible'.")

    headers = {"Authorization": f"Bearer {VISION_API_KEY}"} if VISION_API_KEY else {}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        return body["message"]["content"] if VISION_PROVIDER == "ollama" else body["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise DrawingReadError("The configured vision model is unavailable or returned an unsupported response.") from exc


async def analyse_drawing(pdf_bytes: bytes, filename: str) -> DrawingAnalysisResponse:
    encoded_pages = _render_pdf_pages(pdf_bytes)
    content = await _read_with_vision_model(encoded_pages, filename)
    try:
        raw = json.loads(_strip_code_fence(content))
        rooms = [DrawingRoom.model_validate(item) for item in raw.get("rooms", [])]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise DrawingReadError("The vision model did not return usable room measurements. Try a clearer exported drawing.") from exc

    takeoffs = []
    for room in rooms:
        estimate = calculate_estimate(EstimateInput(length_m=room.length_m, width_m=room.width_m, room_name=room.name, save=False))
        takeoffs.append(DrawingRoomTakeoff(room=room, estimate=estimate))
    return DrawingAnalysisResponse(
        model=VISION_MODEL,
        drawing_notes=[str(note) for note in raw.get("drawing_notes", [])][:20],
        rooms=takeoffs,
        total_panels_to_order=sum(item.estimate.panels_to_order for item in takeoffs),
        total_wall_panels_to_order=sum(item.estimate.wall_panels_to_order for item in takeoffs),
        total_t_beams=sum(item.estimate.beam_count for item in takeoffs),
        total_beam_linear_meters=round(sum(item.estimate.total_beam_linear_meters for item in takeoffs), 2),
    )
