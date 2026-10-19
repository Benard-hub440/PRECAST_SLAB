from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), default="Untitled project")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rooms: Mapped[list["Room"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), default="Room")
    length_m: Mapped[float] = mapped_column(Float)
    width_m: Mapped[float] = mapped_column(Float)
    beam_spacing_m: Mapped[float] = mapped_column(Float, default=1.06)
    panel_run_m: Mapped[float] = mapped_column(Float, default=0.6)
    bearing_depth_m: Mapped[float] = mapped_column(Float, default=0.1)
    fiber_dosage_bags_m2: Mapped[float] = mapped_column(Float, default=0.084)
    project: Mapped[Project | None] = relationship(back_populates="rooms")
    estimates: Mapped[list["Estimate"]] = relationship(back_populates="room", cascade="all, delete-orphan")


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"), nullable=True)
    input_snapshot: Mapped[str] = mapped_column(Text)
    result_snapshot: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    room: Mapped[Room | None] = relationship(back_populates="estimates")
