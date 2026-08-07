from django.db import models

from apps.core.models import TimeStampedModel, Partner


class Transporter(TimeStampedModel):
    """
    A carrier company that physically moves freight for Callum: an airline
    / air cargo operator, an ocean carrier or NVOCC, or a trucking / rail
    company. A Transporter can support more than one mode (e.g. a 3PL
    offering both sea and land legs).
    """

    class Mode(models.TextChoices):
        AIR = "AIR", "Air"
        SEA = "SEA", "Sea"
        LAND = "LAND", "Land"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    modes = models.CharField(
        max_length=20,
        help_text="Comma-separated subset of AIR,SEA,LAND this transporter operates.",
    )
    scac_or_iata = models.CharField(
        max_length=20, blank=True, help_text="SCAC (sea/land) or IATA code (air), if applicable."
    )
    coverage_countries = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated ISO country codes this transporter serves."
    )
    contact_name = models.CharField(max_length=150, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    partner = models.OneToOneField(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transporter",
        help_text="Integration credential this transporter authenticates with, if they push data via API.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def mode_list(self):
        return [m.strip().upper() for m in self.modes.split(",") if m.strip()]

    def operates_mode(self, mode: str) -> bool:
        return mode.upper() in self.mode_list()
