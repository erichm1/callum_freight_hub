from django.contrib import admin

from apps.core.models import Partner, WebhookDeliveryLog


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_type", "is_active", "api_key_preview", "created_at")
    list_filter = ("partner_type", "is_active")
    search_fields = ("name", "contact_email")
    readonly_fields = ("api_key", "created_at", "updated_at")

    @admin.display(description="API key")
    def api_key_preview(self, obj):
        return f"{obj.api_key[:14]}…"


@admin.register(WebhookDeliveryLog)
class WebhookDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "partner", "method", "path", "status_code")
    list_filter = ("method", "status_code")
    search_fields = ("path",)
    readonly_fields = [f.name for f in WebhookDeliveryLog._meta.fields]

    def has_add_permission(self, request):
        return False
