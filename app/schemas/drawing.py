from pydantic import BaseModel, Field

from app.schemas.estimate import EstimateResult


class DrawingRoom(BaseModel):
    """A room measurement reported by the local vision model, in metres."""

    name: str = Field(default="Unlabelled room", max_length=160)
    length_m: float = Field(gt=0, le=1000)
    width_m: float = Field(gt=0, le=1000)
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(default="", max_length=500)


class DrawingRoomTakeoff(BaseModel):
    room: DrawingRoom
    estimate: EstimateResult


class DrawingAnalysisResponse(BaseModel):
    model: str
    drawing_notes: list[str] = []
    rooms: list[DrawingRoomTakeoff]
    total_panels_to_order: int
    total_wall_panels_to_order: int
    total_t_beams: int
    total_beam_linear_meters: float
    review_required: bool = True
