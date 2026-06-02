"""Bounded autoscaler.

Reads per-instance request counters from the shared database, computes the
average requests-per-second across running instances, and scales the API
service up or down within hard min/max bounds. A cooldown prevents rapid
flapping (runaway scaling).
"""
import threading
import time
from datetime import datetime

from sqlalchemy import bindparam, create_engine, text

from app.config import settings
from app.docker_manager import manager


class AutoScaler:
    def __init__(self):
        self.enabled = False
        self.last_action_at = 0.0
        self.last_reason = "idle"
        self.last_rps = 0.0
        self._engine = create_engine(settings.db_url, pool_pre_ping=True)
        self._prev_total = None
        self._prev_time = None
        self._thread = None
        self._stop = threading.Event()

    # ---- state ----
    def status(self) -> dict:
        in_cooldown = (time.time() - self.last_action_at) < settings.cooldown_seconds
        return {
            "enabled": self.enabled,
            "min_instances": settings.min_instances,
            "max_instances": settings.max_instances,
            "cooldown_seconds": settings.cooldown_seconds,
            "in_cooldown": in_cooldown,
            "target_rps_high": settings.target_rps_high,
            "target_rps_low": settings.target_rps_low,
            "current_rps_per_instance": round(self.last_rps, 2),
            "last_reason": self.last_reason,
            "current_instances": manager.current_count(),
        }

    def set_enabled(self, value: bool):
        self.enabled = value
        self.last_reason = "autoscaler enabled" if value else "autoscaler disabled"
        # Reset the RPS baseline so the first tick doesn't see a huge delta.
        self._prev_total = None
        self._prev_time = None

    # ---- metrics ----
    def _total_requests(self) -> int:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT COALESCE(SUM(request_count), 0) FROM instance_heartbeats")
            ).first()
            return int(row[0]) if row else 0

    def _compute_rps_per_instance(self) -> float:
        now = time.time()
        total = self._total_requests()
        if self._prev_total is None or self._prev_time is None:
            self._prev_total, self._prev_time = total, now
            return 0.0
        dt = max(now - self._prev_time, 1e-3)
        delta = max(total - self._prev_total, 0)
        self._prev_total, self._prev_time = total, now
        instances = max(manager.current_count(), 1)
        return (delta / dt) / instances

    # ---- stale heartbeat sweeper ----
    def _sweep_stale_heartbeats(self) -> int:
        """Delete heartbeat rows for instance IDs whose container no longer exists.

        Runs on every tick (even when the autoscaler is disabled) so the
        Backend Instances table stops showing zombie rows after scale-down.
        """
        try:
            live_ids = {c["id"] for c in manager.list_api_containers() if c["status"] == "running"}
        except Exception:
            return 0
        if not live_ids:
            # Don't wipe the table if Docker temporarily reports no containers.
            return 0
        with self._engine.begin() as conn:
            result = conn.execute(
                text(
                    "DELETE FROM instance_heartbeats "
                    "WHERE instance_id NOT IN :live"
                ).bindparams(bindparam("live", expanding=True)),
                {"live": list(live_ids)},
            )
            removed = result.rowcount or 0
        if removed:
            # The next RPS sample would see a negative delta after the deletion;
            # reset so we measure from a clean baseline.
            self._prev_total = None
            self._prev_time = None
        return removed

    # ---- control loop ----
    def _tick(self):
        self._sweep_stale_heartbeats()
        if not self.enabled:
            return
        rps = self._compute_rps_per_instance()
        self.last_rps = rps

        # Respect cooldown.
        if (time.time() - self.last_action_at) < settings.cooldown_seconds:
            self.last_reason = f"cooldown ({rps:.1f} rps/inst)"
            return

        current = manager.current_count()
        if rps > settings.target_rps_high and current < settings.max_instances:
            manager.scale_to(current + 1)
            self.last_action_at = time.time()
            self.last_reason = f"scaled up: {rps:.1f} rps/inst > {settings.target_rps_high}"
        elif rps < settings.target_rps_low and current > settings.min_instances:
            manager.scale_to(current - 1)
            self.last_action_at = time.time()
            self.last_reason = f"scaled down: {rps:.1f} rps/inst < {settings.target_rps_low}"
        else:
            self.last_reason = f"stable ({rps:.1f} rps/inst)"

    def _run(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:  # never let the loop die
                self.last_reason = f"error: {e}"
            self._stop.wait(settings.autoscale_interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()


autoscaler = AutoScaler()
