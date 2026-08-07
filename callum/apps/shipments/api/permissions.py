from rest_framework import permissions

from apps.core.models import Partner


class IsStaffOrPartner(permissions.BasePermission):
    """
    Allows access to authenticated Django staff (console/admin users) or
    to a valid Partner (transporter/gateway) authenticated via API key.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return True
        auth = getattr(request, "auth", None)
        return isinstance(auth, Partner)


class IsOwnerPartnerOrStaff(permissions.BasePermission):
    """
    For write/detail actions: staff can touch anything; a partner can only
    act on shipments they submitted, or that involve a Gateway/Transporter
    they own (so a transporter can update tracking on shipments assigned
    to them even if a different gateway created the record).
    """

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.is_staff:
            return True

        partner = getattr(request, "auth", None)
        if not isinstance(partner, Partner):
            return False

        if obj.submitted_by_id == partner.id:
            return True

        transporter = getattr(partner, "transporter", None)
        if transporter and obj.transporter_id == transporter.id:
            return True

        gateway = getattr(partner, "gateway", None)
        if gateway and obj.origin_gateway_id == gateway.id or gateway and obj.destination_gateway_id == getattr(gateway, "id", None):
            return True

        return request.method in permissions.SAFE_METHODS
