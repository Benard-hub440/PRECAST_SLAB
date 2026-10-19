from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.drawing import DrawingAnalysisResponse
from app.services.drawing_reader import DrawingReadError, analyse_drawing

router = APIRouter(prefix="/drawing", tags=["drawing analysis"])
MAX_DRAWING_BYTES = 15 * 1024 * 1024
PDF_CONTENT_TYPE = "application/pdf"


@router.post("/analyse", response_model=DrawingAnalysisResponse)
async def analyse(upload: UploadFile = File(..., description="Architectural or structural drawing image")):
    if upload.content_type != PDF_CONTENT_TYPE:
        raise HTTPException(415, "Upload a PDF drawing (maximum 15 MB).")
    contents = await upload.read(MAX_DRAWING_BYTES + 1)
    if not contents or len(contents) > MAX_DRAWING_BYTES:
        raise HTTPException(413, "Drawing must be between 1 byte and 15 MB.")
    try:
        return await analyse_drawing(contents, upload.filename or "drawing.pdf")
    except DrawingReadError as exc:
        raise HTTPException(502, str(exc)) from exc
