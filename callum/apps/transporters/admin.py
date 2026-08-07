from django.contrib import admin

from apps.transporters.models import Transporter


@admin.register(Transporter)
class TransporterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "modes", "scac_or_iata", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "scac_or_iata")
