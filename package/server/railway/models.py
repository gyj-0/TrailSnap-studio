"""Railway data models."""

from datetime import date, datetime, time
from enum import Enum
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StationGrade(str, Enum):
    """Railway station grade classification."""

    SPECIAL = "特等站"
    FIRST = "一等站"
    SECOND = "二等站"
    THIRD = "三等站"
    FOURTH = "四等站"
    FIFTH = "五等站"


class RailwayStation(Base):
    """Railway station model."""

    __tablename__ = "railway_stations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Station codes
    station_code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    telegraph_code: Mapped[str | None] = mapped_column(
        String(10), unique=True, index=True, nullable=True
    )
    pinyin_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Names
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    alias_names: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    
    # Location
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Coordinates
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Classification
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    station_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Operational info
    is_operational: Mapped[bool] = mapped_column(default=True, nullable=False)
    opened_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Extra data
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    schedules_as_origin: Mapped[list["TrainSchedule"]] = relationship(  # type: ignore  # noqa: F821
        "TrainSchedule", foreign_keys="TrainSchedule.origin_station_id", back_populates="origin_station"
    )
    schedules_as_destination: Mapped[list["TrainSchedule"]] = relationship(  # type: ignore  # noqa: F821
        "TrainSchedule", foreign_keys="TrainSchedule.destination_station_id", back_populates="destination_station"
    )

    def __repr__(self) -> str:
        return f"<RailwayStation({self.station_code}: {self.name})>"


class TrainLine(Base):
    """Railway line model."""

    __tablename__ = "train_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Line info
    line_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    line_name: Mapped[str] = mapped_column(String(200), nullable=False)
    line_name_en: Mapped[str | None] = mapped_column(String(300), nullable=True)
    
    # Classification
    line_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    speed_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Route
    origin_station_id: Mapped[int | None] = mapped_column(
        ForeignKey("railway_stations.id"), nullable=True
    )
    destination_station_id: Mapped[int | None] = mapped_column(
        ForeignKey("railway_stations.id"), nullable=True
    )
    
    # Distance
    total_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Extra data
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    schedules: Mapped[list["TrainSchedule"]] = relationship("TrainSchedule", back_populates="line")  # type: ignore  # noqa: F821


class TrainSchedule(Base):
    """Train schedule model."""

    __tablename__ = "train_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Train info
    train_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    train_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Line reference
    line_id: Mapped[int | None] = mapped_column(
        ForeignKey("train_lines.id"), nullable=True
    )
    
    # Stations
    origin_station_id: Mapped[int] = mapped_column(
        ForeignKey("railway_stations.id"), nullable=False
    )
    destination_station_id: Mapped[int] = mapped_column(
        ForeignKey("railway_stations.id"), nullable=False
    )
    
    # Schedule times
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    arrival_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    
    # Duration (in minutes)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Distance
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Operational info
    operating_days: Mapped[list[int] | None] = mapped_column(
        JSONB, nullable=True
    )  # [0-6] for days of week
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Extra data
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    line: Mapped["TrainLine | None"] = relationship("TrainLine", back_populates="schedules")  # type: ignore  # noqa: F821
    origin_station: Mapped["RailwayStation"] = relationship(  # type: ignore  # noqa: F821
        "RailwayStation", foreign_keys=[origin_station_id], back_populates="schedules_as_origin"
    )
    destination_station: Mapped["RailwayStation"] = relationship(  # type: ignore  # noqa: F821
        "RailwayStation", foreign_keys=[destination_station_id], back_populates="schedules_as_destination"
    )
