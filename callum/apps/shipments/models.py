import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, Partner
from apps.gateways.models import Gateway
from apps.transporters.models import Transporter
from apps.shipments.mode_schemas import validate_metadata


def new_reference() -> str:
    return f"CLM-{uuid.uuid4().hex[:10].upper()}"


class Shipment(TimeStampedModel):
    """
    A single shipment moving through the Callum network. One model covers
    all three transport modes: the `mode` field selects air/sea/land, and
    mode-specific details (AWB/BL/waybill numbers, vessel, flight, etc.)
    live in `metadata` (JSON) rather than mode-specific tables, so new
    partner fields don't require a schema migration.
    """

    class Mode(models.TextChoices):
        AIR = "AIR", "Air"
        SEA = "SEA", "Sea"
        LAND = "LAND", "Land"

    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        PICKED_UP = "PICKED_UP", "Picked up"
        IN_TRANSIT = "IN_TRANSIT", "In transit"
        AT_GATEWAY = "AT_GATEWAY", "At gateway"
        CUSTOMS_HOLD = "CUSTOMS_HOLD", "Customs hold"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Out for delivery"
        DELIVERED = "DELIVERED", "Delivered"
        EXCEPTION = "EXCEPTION", "Exception"
        CANCELLED = "CANCELLED", "Cancelled"

    reference = models.CharField(max_length=30, unique=True, default=new_reference, editable=False)
    mode = models.CharField(max_length=10, choices=Mode.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    origin_gateway = models.ForeignKey(
        Gateway, on_delete=models.PROTECT, related_name="departing_shipments"
    )
    destination_gateway = models.ForeignKey(
        Gateway, on_delete=models.PROTECT, related_name="arriving_shipments"
    )
    transporter = models.ForeignKey(
        Transporter, on_delete=models.PROTECT, related_name="shipments"
    )
    submitted_by = models.ForeignKey(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_shipments",
        help_text="Partner (transporter or gateway) that created this shipment via the API, if any.",
    )

    shipper_name = models.CharField(max_length=150, blank=True)
    consignee_name = models.CharField(max_length=150, blank=True)
    description_of_goods = models.CharField(max_length=255, blank=True)

    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    pieces = models.PositiveIntegerField(null=True, blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mode-specific details (AWB/BL/waybill numbers, vessel, flight, container, etc.)",
    )

    etd = models.DateTimeField(null=True, blank=True, verbose_name="Estimated departure")
    eta = models.DateTimeField(null=True, blank=True, verbose_name="Estimated arrival")
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mode", "status"]),
            models.Index(fields=["reference"]),
        ]

    def __str__(self):
        return f"{self.reference} [{self.mode}] {self.origin_gateway.code} → {self.destination_gateway.code}"

    def clean(self):
        errors = {}

        if self.transporter_id and not self.transporter.operates_mode(self.mode):
            errors["transporter"] = (
                f"{self.transporter.name} does not operate {self.get_mode_display()} transport."
            )

        if self.origin_gateway_id and not self.origin_gateway.supports_mode(self.mode):
            errors["origin_gateway"] = f"{self.origin_gateway.code} does not support {self.get_mode_display()}."

        if self.destination_gateway_id and not self.destination_gateway.supports_mode(self.mode):
            errors["destination_gateway"] = (
                f"{self.destination_gateway.code} does not support {self.get_mode_display()}."
            )

        if self.origin_gateway_id and self.destination_gateway_id and self.origin_gateway_id == self.destination_gateway_id:
            errors["destination_gateway"] = "Origin and destination gateway must differ."

        metadata_errors = validate_metadata(self.mode, self.metadata or {})
        if metadata_errors:
            errors["metadata"] = metadata_errors

        if errors:
            raise ValidationError(errors)

    def record_event(self, status, location="", description="", source="INTERNAL"):
        event = self.events.create(
            status=status,
            location=location,
            description=description,
            source=source,
        )
        self.status = status
        self.save(update_fields=["status", "updated_at"])
        return event


class ShipmentEvent(TimeStampedModel):
    """
    A single tracking milestone in a shipment's life. The combination of
    a Shipment's events forms the timeline shown in the console and
    returned by the tracking API endpoint.
    """

    class Source(models.TextChoices):
        INTERNAL = "INTERNAL", "Callum (internal)"
        TRANSPORTER = "TRANSPORTER", "Transporter feed"
        GATEWAY = "GATEWAY", "Partner gateway feed"

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=20, choices=Shipment.Status.choices)
    location = models.CharField(max_length=150, blank=True)
    description = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=15, choices=Source.choices, default=Source.INTERNAL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shipment.reference}: {self.get_status_display()} @ {self.location or '—'}"
