import time
from dataclasses import dataclass, field

__all__ = ["RateLimiter"]


@dataclass
class RateLimiter:
    """
    Very small in-memory fixed-window rate limiter.

    Notes:
    - This is per-process (not global across instances).
    - Good enough for early-stage abuse protection.
    """

    buckets: dict[str, tuple[int, float]] = field(default_factory=dict)

    def allow(self, *, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        count, reset_at = self.buckets.get(key, (0, now + window_seconds))
        if now >= reset_at:
            count, reset_at = 0, now + window_seconds
        count += 1
        self.buckets[key] = (count, reset_at)
        return count <= limit

