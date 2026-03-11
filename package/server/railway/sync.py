"""Railway data synchronization service."""

from datetime import datetime
from typing import Any

import aiohttp
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger

from .models import RailwayStation, TrainLine, TrainSchedule

logger = get_logger(__name__)


class RailwaySyncService:
    """Service for synchronizing railway data from external sources."""

    def __init__(self):
        self.api_base_url = settings.RAILWAY_API_BASE_URL
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch_data(self, endpoint: str) -> list[dict[str, Any]]:
        """Fetch data from API endpoint."""
        session = await self._get_session()
        url = f"{self.api_base_url}/{endpoint}"
        
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch data from {url}: {e}")
            raise

    async def sync_stations(self, db: AsyncSession) -> dict[str, int]:
        """
        Synchronize railway stations.
        
        Returns:
            Dict with sync results
        """
        logger.info("Starting railway station sync")
        
        try:
            stations_data = await self._fetch_data("stations")
        except Exception as e:
            logger.error(f"Failed to fetch stations: {e}")
            return {"created": 0, "updated": 0, "failed": 0}

        created = 0
        updated = 0
        failed = 0

        for station_data in stations_data:
            try:
                # Upsert station data
                stmt = insert(RailwayStation).values(
                    station_code=station_data.get("code"),
                    telegraph_code=station_data.get("telegraph_code"),
                    pinyin_code=station_data.get("pinyin_code"),
                    name=station_data.get("name"),
                    name_en=station_data.get("name_en"),
                    alias_names=station_data.get("aliases", []),
                    province=station_data.get("province"),
                    city=station_data.get("city"),
                    district=station_data.get("district"),
                    address=station_data.get("address"),
                    latitude=station_data.get("latitude"),
                    longitude=station_data.get("longitude"),
                    grade=station_data.get("grade"),
                    station_type=station_data.get("type"),
                    is_operational=station_data.get("is_operational", True),
                    extra_data=station_data.get("extra"),
                )
                
                # Update on conflict
                stmt = stmt.on_conflict_do_update(
                    index_elements=["station_code"],
                    set_={
                        "name": stmt.excluded.name,
                        "telegraph_code": stmt.excluded.telegraph_code,
                        "latitude": stmt.excluded.latitude,
                        "longitude": stmt.excluded.longitude,
                        "updated_at": datetime.utcnow(),
                    },
                )
                
                result = await db.execute(stmt)
                
                if result.rowcount > 0:
                    # Check if it was an insert or update
                    existing = await db.execute(
                        select(RailwayStation).where(
                            RailwayStation.station_code == station_data.get("code")
                        )
                    )
                    if existing.scalar_one_or_none():
                        updated += 1
                    else:
                        created += 1

            except Exception as e:
                logger.error(f"Failed to sync station {station_data.get('code')}: {e}")
                failed += 1

        await db.commit()
        logger.info(f"Station sync complete: {created} created, {updated} updated, {failed} failed")
        
        return {"created": created, "updated": updated, "failed": failed}

    async def sync_lines(self, db: AsyncSession) -> dict[str, int]:
        """
        Synchronize railway lines.
        
        Returns:
            Dict with sync results
        """
        logger.info("Starting railway line sync")
        
        try:
            lines_data = await self._fetch_data("lines")
        except Exception as e:
            logger.error(f"Failed to fetch lines: {e}")
            return {"created": 0, "updated": 0, "failed": 0}

        created = 0
        updated = 0
        failed = 0

        for line_data in lines_data:
            try:
                stmt = insert(TrainLine).values(
                    line_code=line_data.get("code"),
                    line_name=line_data.get("name"),
                    line_name_en=line_data.get("name_en"),
                    line_type=line_data.get("type"),
                    speed_grade=line_data.get("speed_grade"),
                    total_distance=line_data.get("distance"),
                    extra_data=line_data.get("extra"),
                )
                
                stmt = stmt.on_conflict_do_update(
                    index_elements=["line_code"],
                    set_={
                        "line_name": stmt.excluded.line_name,
                        "total_distance": stmt.excluded.total_distance,
                        "updated_at": datetime.utcnow(),
                    },
                )
                
                result = await db.execute(stmt)
                
                if result.rowcount > 0:
                    updated += 1
                else:
                    created += 1

            except Exception as e:
                logger.error(f"Failed to sync line {line_data.get('code')}: {e}")
                failed += 1

        await db.commit()
        logger.info(f"Line sync complete: {created} created, {updated} updated, {failed} failed")
        
        return {"created": created, "updated": updated, "failed": failed}

    async def sync_schedules(self, db: AsyncSession) -> dict[str, int]:
        """
        Synchronize train schedules.
        
        Returns:
            Dict with sync results
        """
        logger.info("Starting train schedule sync")
        
        try:
            schedules_data = await self._fetch_data("schedules")
        except Exception as e:
            logger.error(f"Failed to fetch schedules: {e}")
            return {"created": 0, "updated": 0, "failed": 0}

        created = 0
        updated = 0
        failed = 0

        for schedule_data in schedules_data:
            try:
                # Get station IDs
                origin_station = await db.execute(
                    select(RailwayStation.id).where(
                        RailwayStation.station_code == schedule_data.get("origin_code")
                    )
                )
                origin_id = origin_station.scalar_one_or_none()
                
                destination_station = await db.execute(
                    select(RailwayStation.id).where(
                        RailwayStation.station_code == schedule_data.get("destination_code")
                    )
                )
                destination_id = destination_station.scalar_one_or_none()
                
                if not origin_id or not destination_id:
                    logger.warning(
                        f"Skipping schedule {schedule_data.get('train_number')}: "
                        f"stations not found"
                    )
                    failed += 1
                    continue

                stmt = insert(TrainSchedule).values(
                    train_number=schedule_data.get("train_number"),
                    train_type=schedule_data.get("train_type"),
                    origin_station_id=origin_id,
                    destination_station_id=destination_id,
                    departure_time=schedule_data.get("departure_time"),
                    arrival_time=schedule_data.get("arrival_time"),
                    duration_minutes=schedule_data.get("duration"),
                    distance_km=schedule_data.get("distance"),
                    operating_days=schedule_data.get("operating_days"),
                    extra_data=schedule_data.get("extra"),
                )
                
                stmt = stmt.on_conflict_do_update(
                    index_elements=["train_number"],
                    set_={
                        "departure_time": stmt.excluded.departure_time,
                        "arrival_time": stmt.excluded.arrival_time,
                        "updated_at": datetime.utcnow(),
                    },
                )
                
                result = await db.execute(stmt)
                
                if result.rowcount > 0:
                    updated += 1
                else:
                    created += 1

            except Exception as e:
                logger.error(
                    f"Failed to sync schedule {schedule_data.get('train_number')}: {e}"
                )
                failed += 1

        await db.commit()
        logger.info(
            f"Schedule sync complete: {created} created, {updated} updated, {failed} failed"
        )
        
        return {"created": created, "updated": updated, "failed": failed}

    async def sync_all(self, db: AsyncSession) -> dict[str, dict[str, int]]:
        """
        Synchronize all railway data.
        
        Returns:
            Dict with sync results for each entity type
        """
        logger.info("Starting full railway data sync")
        
        results = {
            "stations": await self.sync_stations(db),
            "lines": await self.sync_lines(db),
            "schedules": await self.sync_schedules(db),
        }
        
        logger.info("Full railway data sync complete")
        return results


# Global sync service instance
railway_sync = RailwaySyncService()
