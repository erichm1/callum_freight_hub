from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

from apps.core.models import Partner


class PartnerAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Authenticates transporters and partner gateways against Callum's API
    using a static key sent in the `X-Callum-Api-Key` header. This is the
    primary auth path for machine-to-machine integrations; staff using the
    console authenticate via session/token instead.
    """

    header_name = getattr(settings, "CALLUM_API_KEY_HEADER", "X-Callum-Api-Key")

    def authenticate(self, request):
        api_key = request.headers.get(self.header_name)
        if not api_key:
            return None

        try:
            partner = Partner.objects.get(api_key=api_key, is_active=True)
        except Partner.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid or inactive API key."))

        if partner.allowed_ips:
            remote_ip = request.META.get("REMOTE_ADDR", "")
            allowed = [ip.strip() for ip in partner.allowed_ips.split(",") if ip.strip()]
            if allowed and remote_ip not in allowed:
                raise exceptions.AuthenticationFailed(_("Source IP not allowed for this partner."))

        # Callum treats the authenticated Partner as the request principal.
        # Downstream views can access request.auth to know which partner
        # (transporter / gateway) is calling.
        return (partner, None)

    def authenticate_header(self, request):
        return self.header_name
