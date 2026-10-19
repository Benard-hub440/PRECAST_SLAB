from app.schemas.estimate import EstimateInput
from app.services.calculator import calculate_estimate


def test_5_by_4_room_uses_short_span_and_boundary_beam():
    result = calculate_estimate(EstimateInput(length_m=5, width_m=4, save=False))
    assert result.span_m == 4
    assert result.distribution_m == 5
    assert result.bay_count == 5
    assert result.beam_count == 6
    assert result.total_beam_linear_meters == 24
    assert result.theoretical_panels == 20
    assert result.panels_to_order == 24
    assert result.fiber_bags == 2


def test_ten_percent_panel_buffer_wins_when_larger_than_four():
    result = calculate_estimate(EstimateInput(length_m=20, width_m=20, save=False))
    assert result.panel_buffer == 38


def test_one_metre_slab_and_three_metre_wall_panels_are_counted_separately():
    result = calculate_estimate(EstimateInput(length_m=5, width_m=4, save=False))
    assert result.panels_per_bay == 4
    assert result.theoretical_panels == 20
    assert result.panels_to_order == 24
    assert result.wall_perimeter_m == 18
    assert result.theoretical_wall_panels == 6
    assert result.wall_panels_to_order == 7
