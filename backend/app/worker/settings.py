"""Arq WorkerSettings configuration."""

from arq.connections import RedisSettings
from backend.app.config import settings
from backend.app.worker.tasks import process_inbound


class WorkerSettings:
    functions = [process_inbound]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 20
    poll_delay = 0.5
