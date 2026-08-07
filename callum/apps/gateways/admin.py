from django.contrib import admin

from apps.gateways.models import Gateway


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "country", "city", "modes", "is_active")
    list_filter = ("kind", "is_active", "supports_air", "supports_sea", "supports_land")
    search_fields = ("code", "name", "city")

    @admin.display(description="Modes")
    def modes(self, obj):
        modes = []
        if obj.supports_air:
            modes.append("Air")
        if obj.supports_sea:
            modes.append("Sea")
        if obj.supports_land:
            modes.append("Land")
        return ", ".join(modes) or "—"
