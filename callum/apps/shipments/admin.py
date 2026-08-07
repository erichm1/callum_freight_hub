from django.contrib import admin

from apps.shipments.models import Shipment, ShipmentEvent


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("status", "location", "description", "source", "created_at")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("reference", "mode", "status", "origin_gateway", "destination_gateway", "transporter", "eta")
    list_filter = ("mode", "status", "transporter")
    search_fields = ("reference", "shipper_name", "consignee_name")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [ShipmentEventInline]
    autocomplete_fields = ("origin_gateway", "destination_gateway", "transporter")


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ("shipment", "status", "location", "source", "created_at")
    list_filter = ("status", "source")
