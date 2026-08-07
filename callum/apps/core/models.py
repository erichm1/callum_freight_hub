import secrets
import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base carrying created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def generate_api_key() -> str:
    return f"callum_{secrets.token_urlsafe(32)}"


class Partner(TimeStampedModel):
    """
    Credential representing an external system that integrates with Callum:
    a transporter's system, or another gateway. One Partner may map to a
    Transporter and/or a Gateway record (see those apps), or stand alone.
    """

    class PartnerType(models.TextChoices):
        TRANSPORTER = "TRANSPORTER", "Transporter"
        GATEWAY = "GATEWAY", "Partner gateway"
        INTERNAL = "INTERNAL", "Internal system"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices)
    api_key = models.CharField(max_length=128, unique=True, default=generate_api_key, editable=False)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    allowed_ips = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated CIDR/IP allowlist. Empty = no IP restriction.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"

    def rotate_key(self) -> str:
        self.api_key = generate_api_key()
        self.save(update_fields=["api_key"])
        return self.api_key


class WebhookDeliveryLog(TimeStampedModel):
    """Audit trail of inbound partner API calls for traceability/debugging."""

    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests")
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    payload_summary = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.path} -> {self.status_code}"
