from pydantic import BaseModel, Field

from app.schemas.estimate import EstimateInput, EstimateResult


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    estimate_input: EstimateInput | None = None


class ChatResponse(BaseModel):
    answer: str
    tool_used: str | None = None
    estimate: EstimateResult | None = None
