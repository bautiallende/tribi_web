"""Async background scheduler that runs support automation jobs."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime

from ..core.config import settings
from .tickets import run_support_digest, run_ticket_sla_cycle

logger = logging.getLogger(__name__)


class BackgroundJobScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._shutdown = asyncio.Event()
        self._last_daily_digest: date | None = None
        self._last_weekly_digest: date | None = None
        self._is_running = False

    async def start(self) -> None:
        if not settings.JOB_ENABLED:
            logger.info("Job scheduler disabled via settings")
            return
        if self._task is not None:
            return
        self._shutdown = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())
        self._is_running = True
        logger.info("Background job scheduler started")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._shutdown.set()
        await self._task
        self._task = None
        self._is_running = False
        logger.info("Background job scheduler stopped")

    async def _run_loop(self) -> None:
        interval = max(30, settings.JOB_LOOP_INTERVAL_SECONDS)
        while not self._shutdown.is_set():
            started = time.monotonic()
            try:
                await asyncio.to_thread(self._run_cycle)
            except Exception:  # pragma: no cover - safety net
                logger.exception("Background job cycle failed")
            elapsed = time.monotonic() - started
            wait_time = max(0.0, interval - elapsed)
            try:
                await asyncio.wait_for(self._shutdown.wait(), timeout=wait_time)
            except asyncio.TimeoutError:
                continue

    def _run_cycle(self) -> None:
        now = datetime.utcnow()
        stats = run_ticket_sla_cycle(now)
        if stats["reminders"] or stats["escalations"]:
            logger.info("Ticket SLA job", extra={"metrics": stats})
        self._maybe_run_digests(now)

    def _maybe_run_digests(self, now: datetime) -> None:
        if self._should_run_daily_digest(now):
            run_support_digest(now, cadence="daily")
            self._last_daily_digest = now.date()
        if self._should_run_weekly_digest(now):
            run_support_digest(now, cadence="weekly")
            self._last_weekly_digest = now.date()

    def _should_run_daily_digest(self, now: datetime) -> bool:
        if now.hour < settings.SUPPORT_DIGEST_HOUR_UTC:
            return False
        return self._last_daily_digest != now.date()

    def _should_run_weekly_digest(self, now: datetime) -> bool:
        if now.weekday() != 0:  # Monday
            return False
        if now.hour < settings.SUPPORT_DIGEST_HOUR_UTC:
            return False
        return self._last_weekly_digest != now.date()

    def status(self) -> dict[str, object]:
        return {
            "enabled": bool(settings.JOB_ENABLED),
            "running": self._is_running and self._task is not None,
            "last_daily_digest": (
                self._last_daily_digest.isoformat() if self._last_daily_digest else None
            ),
            "last_weekly_digest": (
                self._last_weekly_digest.isoformat()
                if self._last_weekly_digest
                else None
            ),
        }


def get_job_scheduler() -> BackgroundJobScheduler:
    return BackgroundJobScheduler()
