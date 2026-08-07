from django.conf import settings


class PartnerAPIKeyAuditMiddleware:
    """
    Logs a lightweight audit trail for requests hitting the partner-facing
    API, so integration issues (bad payloads, auth failures) can be traced
    back to a specific transporter or gateway. Kept intentionally simple —
    swap for structured logging / APM in production.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/api/v1/") and request.headers.get(settings.CALLUM_API_KEY_HEADER):
            self._log(request, response)

        return response

    @staticmethod
    def _log(request, response):
        # Deferred import to avoid touching the DB during app startup / migrations.
        from apps.core.models import WebhookDeliveryLog

        partner = getattr(getattr(request, "auth", None), "id", None) and request.auth
        try:
            WebhookDeliveryLog.objects.create(
                partner=partner if partner else None,
                method=request.method,
                path=request.path[:255],
                status_code=response.status_code,
                payload_summary=str(request.body[:500]) if request.method in ("POST", "PATCH", "PUT") else "",
            )
        except Exception:
            # Never let audit logging break the actual request/response cycle.
            pass
