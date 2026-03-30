"""Simple rate limiter for API endpoints"""

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request


class RateLimiter:
    """Token bucket rate limiter per client IP"""

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def __call__(self, request: Request):
        if request.client is None:
            raise HTTPException(status_code=400, detail="Client address unavailable")
        client = request.client.host
        now = time.time()

        # Clean old requests outside window
        self.requests[client] = [
            t for t in self.requests[client] if now - t < self.period
        ]

        # Check limit
        if len(self.requests[client]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.calls} requests per {self.period}s",
            )

        self.requests[client].append(now)
        return True


# 10 messages per minute for send endpoint
send_limiter = RateLimiter(calls=10, period=60)

# 5 login attempts per 5 minutes per IP
login_limiter = RateLimiter(calls=5, period=300)
