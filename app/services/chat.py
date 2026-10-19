"""Rule-grounded assistant that calls the same calculator used by the API."""
import re

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.estimate import EstimateInput
from app.services.calculator import calculate_estimate


DIMENSION_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m(?:et(?:er|re)s?)?)?\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:m(?:et(?:er|re)s?)?)?", re.I)
SPACING_PATTERN = re.compile(r"(?:spacing|spaced?)\s*(?:is|of|to|at)?\s*(\d+(?:\.\d+)?)\s*m?", re.I)


def _input_from_message(message: str) -> EstimateInput | None:
    dimensions = DIMENSION_PATTERN.search(message)
    if not dimensions:
        return None
    spacing = SPACING_PATTERN.search(message)
    return EstimateInput(
        length_m=float(dimensions.group(1)),
        width_m=float(dimensions.group(2)),
        beam_spacing_m=float(spacing.group(1)) if spacing else 1.06,
        save=False,
    )


def respond_to_chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    normalized = message.lower()
    estimate_input = request.estimate_input or _input_from_message(message)

    # This is the assistant's internal tool call: all numerical replies use the approved engine.
    if estimate_input:
        result = calculate_estimate(estimate_input)
        answer = (
            f"For a {estimate_input.length_m:g} m x {estimate_input.width_m:g} m room, beams span the "
            f"{result.span_m:g} m {result.span_orientation} because it is the shorter dimension. "
            f"That gives {result.bay_count} bays, {result.beam_count} T-beams ({result.total_beam_linear_meters:g} LM), "
            f"and {result.panels_to_order} panels to order ({result.theoretical_panels} theoretical + {result.panel_buffer} buffer). "
            f"Gross screed footprint is {result.gross_screed_area_m2:g} m2, requiring {result.fiber_bags} fiber bags."
        )
        return ChatResponse(answer=answer, tool_used="calculate_estimate", estimate=result)

    if any(word in normalized for word in ("extra beam", "add 1", "n + 1", "n+1")):
        return ChatResponse(answer="Each bay is the space between two beams. For n bays, boundary closure needs n + 1 beam lines: one at each outer edge and one between every adjacent bay.")
    if "spacing" in normalized:
        return ChatResponse(answer="Beam spacing controls bay count: bays = ceil(distribution / spacing), where distribution is the longer room dimension. Larger spacing can reduce bays, beams, and panels, but structural capacity must be verified separately by the engineer.")
    if any(word in normalized for word in ("buffer", "waste", "breakage", "panels")):
        return ChatResponse(answer="Panel ordering adds max(4, ceil(10% of theoretical panels)) to cover site cuts and breakage. Theoretical panels are bays x ceil(span / panel run).")
    if any(word in normalized for word in ("fiber", "screed")):
        return ChatResponse(answer="Gross screed area includes bearing at both edges: (span + 2 x bearing) x (distribution + 2 x bearing). Fiber bags are rounded up from gross area x dosage rate.")
    return ChatResponse(answer="I can explain the takeoff rules or calculate a room. Try: 'How many panels for a 5 x 4 m room?' or provide dimensions in the estimator.")
