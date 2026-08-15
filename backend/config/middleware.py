"""Request middleware."""

import logging
import time

logger = logging.getLogger("request")


class TimingMiddleware:
    """Measure how long a request took and report it.

    The duration is exposed to the caller through a response header and
    written to the request log so slow endpoints are easy to spot.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000

        response["X-Response-Time"] = f"{duration_ms:.2f}ms"
        logger.info(
            "request handled",
            extra={
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
