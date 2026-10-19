import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Estimate, Room
from app.schemas.estimate import EstimateInput, EstimateResponse
from app.services.calculator import calculate_estimate

router = APIRouter(prefix="/estimate", tags=["estimate"])


@router.post("", response_model=EstimateResponse)
def create_estimate(payload: EstimateInput, db: Session = Depends(get_db)):
    result = calculate_estimate(payload)
    if payload.save:
        room = Room(
            project_id=payload.project_id,
            name=payload.room_name,
            length_m=payload.length_m,
            width_m=payload.width_m,
            beam_spacing_m=payload.beam_spacing_m,
            panel_run_m=payload.panel_run_m,
            bearing_depth_m=payload.bearing_depth_m,
            fiber_dosage_bags_m2=payload.fiber_dosage_bags_m2,
        )
        db.add(room)
        db.flush()
        saved = Estimate(room_id=room.id, input_snapshot=payload.model_dump_json(), result_snapshot=result.model_dump_json())
        db.add(saved)
        db.commit()
        db.refresh(saved)
        result.saved_estimate_id = saved.id
    return EstimateResponse(inputs=payload, result=result)
