"""Liveness endpoint shared by every service in the platform."""

from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
    """Return a fixed payload so orchestration can probe the service."""
    return JsonResponse({"status": "ok"})
