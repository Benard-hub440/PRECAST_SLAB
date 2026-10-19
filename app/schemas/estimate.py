from pydantic import BaseModel, ConfigDict, Field


class EstimateInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"length_m": 5, "width_m": 4}})

    length_m: float = Field(gt=0, le=1000, description="Internal room length in metres")
    width_m: float = Field(gt=0, le=1000, description="Internal room width in metres")
    beam_spacing_m: float = Field(default=1.06, gt=0, le=10)
    panel_run_m: float = Field(default=1.0, gt=0, le=10, description="Slab panel coverage along the beam in metres")
    wall_panel_length_m: float = Field(default=3.0, gt=0, le=50, description="Wall panel length in metres")
    bearing_depth_m: float = Field(default=0.1, ge=0, le=1)
    fiber_dosage_bags_m2: float = Field(default=0.084, ge=0, le=10)
    project_id: int | None = Field(default=None, gt=0)
    room_name: str = Field(default="Room", min_length=1, max_length=160)
    save: bool = True


class EstimateResult(BaseModel):
    span_m: float
    distribution_m: float
    span_orientation: str
    bay_count: int
    beam_count: int
    total_beam_linear_meters: float
    panels_per_bay: int
    theoretical_panels: int
    panel_buffer: int
    panels_to_order: int
    wall_perimeter_m: float
    theoretical_wall_panels: int
    wall_panel_buffer: int
    wall_panels_to_order: int
    gross_screed_area_m2: float
    fiber_bags: int
    saved_estimate_id: int | None = None


class EstimateResponse(BaseModel):
    inputs: EstimateInput
    result: EstimateResult
