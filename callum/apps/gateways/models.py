from django.db import models

from apps.core.models import TimeStampedModel, Partner


class Gateway(TimeStampedModel):
    """
    A freight gateway node in the network: either Callum itself (the hub)
    or a partner gateway it exchanges shipments with. Shipments reference
    an origin and destination Gateway, which is what lets Callum act as
    the connective hub between many transporters and many other gateways.
    """

    class GatewayKind(models.TextChoices):
        HUB = "HUB", "Callum (this hub)"
        PARTNER = "PARTNER", "Partner gateway"

    code = models.CharField(max_length=20, unique=True, help_text="Short unique code, e.g. CALLUM-HUB, MEX-GDL-01")
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=10, choices=GatewayKind.choices, default=GatewayKind.PARTNER)
    country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2, e.g. US, MX, DE")
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    supports_air = models.BooleanField(default=True)
    supports_sea = models.BooleanField(default=True)
    supports_land = models.BooleanField(default=True)

    partner = models.OneToOneField(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gateway",
        help_text="Integration credential this gateway authenticates with, if external.",
    )
    inbound_webhook_url = models.URLField(
        blank=True, help_text="Endpoint Callum calls to push shipment updates to this gateway."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def supports_mode(self, mode: str) -> bool:
        return {
            "AIR": self.supports_air,
            "SEA": self.supports_sea,
            "LAND": self.supports_land,
        }.get(mode, False)
