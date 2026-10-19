"""Pure, reusable engineering takeoff calculations."""
from math import ceil

from app.schemas.estimate import EstimateInput, EstimateResult


def calculate_estimate(data: EstimateInput) -> EstimateResult:
    """Apply the approved inverted T-beam and infill panel takeoff methodology."""
    span = min(data.length_m, data.width_m)
    distribution = max(data.length_m, data.width_m)
    orientation = "length" if data.length_m <= data.width_m else "width"
    bays = ceil(distribution / data.beam_spacing_m)
    beams = bays + 1
    panels_per_bay = ceil(span / data.panel_run_m)
    theoretical_panels = bays * panels_per_bay
    panel_buffer = max(4, ceil(0.10 * theoretical_panels))
    # Wall panels are counted around the room perimeter.  They are kept separate
    # from the 1 m slab panels because they are a different 3 m product.
    wall_perimeter = 2 * (data.length_m + data.width_m)
    theoretical_wall_panels = ceil(wall_perimeter / data.wall_panel_length_m)
    wall_panel_buffer = max(1, ceil(0.10 * theoretical_wall_panels))
    gross_area = (span + 2 * data.bearing_depth_m) * (distribution + 2 * data.bearing_depth_m)

    return EstimateResult(
        span_m=round(span, 3),
        distribution_m=round(distribution, 3),
        span_orientation=orientation,
        bay_count=bays,
        beam_count=beams,
        total_beam_linear_meters=round(beams * span, 2),
        panels_per_bay=panels_per_bay,
        theoretical_panels=theoretical_panels,
        panel_buffer=panel_buffer,
        panels_to_order=theoretical_panels + panel_buffer,
        wall_perimeter_m=round(wall_perimeter, 2),
        theoretical_wall_panels=theoretical_wall_panels,
        wall_panel_buffer=wall_panel_buffer,
        wall_panels_to_order=theoretical_wall_panels + wall_panel_buffer,
        gross_screed_area_m2=round(gross_area, 2),
        fiber_bags=ceil(gross_area * data.fiber_dosage_bags_m2),
    )
