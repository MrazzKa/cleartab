"""Simple in-memory limits for the document reader on a public server.

The reader calls a free-tier model API with a daily token cap, so one visitor (or a bot) must not use it up.
Limits are per client address and global, counted in memory only (nothing written to disk, addresses never
logged). Set READ_LIMIT_PER_HOUR, READ_LIMIT_PER_DAY and READ_LIMIT_GLOBAL_DAY to change them; 0 disables a limit.
"""
import os
import threading
import time
from collections import defaultdict, deque

HOUR = 3600
DAY = 86400


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class ReadLimiter:
    def __init__(self, per_hour: int | None = None, per_day: int | None = None, global_day: int | None = None):
        self.per_hour = _env_int("READ_LIMIT_PER_HOUR", 6) if per_hour is None else per_hour
        self.per_day = _env_int("READ_LIMIT_PER_DAY", 15) if per_day is None else per_day
        self.global_day = _env_int("READ_LIMIT_GLOBAL_DAY", 150) if global_day is None else global_day
        self._by_client: dict[str, deque[float]] = defaultdict(deque)
        self._all: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self, client: str, now: float | None = None) -> str | None:
        """Record one read for this client and return None, or return the reason it is refused."""
        now = time.time() if now is None else now
        with self._lock:
            while self._all and now - self._all[0] > DAY:
                self._all.popleft()
            hits = self._by_client[client]
            while hits and now - hits[0] > DAY:
                hits.popleft()
            if not hits:
                self._by_client.pop(client, None)
                hits = self._by_client[client]
            if self.global_day and len(self._all) >= self.global_day:
                return "Document reading has reached today's limit for everyone. You can still type the amounts."
            if self.per_day and len(hits) >= self.per_day:
                return "You have reached today's limit for reading documents. You can still type the amounts."
            if self.per_hour and sum(1 for t in hits if now - t <= HOUR) >= self.per_hour:
                return "Too many documents in the last hour. Please try again later or type the amounts."
            hits.append(now)
            self._all.append(now)
            return None
