from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from apps.gateways.models import Gateway
from apps.transporters.models import Transporter
from apps.shipments.models import Shipment, ShipmentEvent
from apps.shipments.mode_schemas import MODE_SCHEMAS
from apps.shipments.api.serializers import (
    GatewaySerializer,
    TransporterSerializer,
    ShipmentSerializer,
    ShipmentEventSerializer,
    ShipmentEventCreateSerializer,
    ModeSchemaSerializer,
)
from apps.shipments.api.filters import ShipmentFilter
from apps.shipments.api.permissions import IsStaffOrPartner, IsOwnerPartnerOrStaff


class GatewayViewSet(viewsets.ReadOnlyModelViewSet):
    """List/retrieve every gateway in the network — Callum plus partners."""

    queryset = Gateway.objects.filter(is_active=True)
    serializer_class = GatewaySerializer
    permission_classes = [IsStaffOrPartner]
    filterset_fields = ["kind", "country", "supports_air", "supports_sea", "supports_land"]
    search_fields = ["code", "name", "city"]


class TransporterViewSet(viewsets.ReadOnlyModelViewSet):
    """List/retrieve transporters registered with the hub."""

    queryset = Transporter.objects.filter(is_active=True)
    serializer_class = TransporterSerializer
    permission_classes = [IsStaffOrPartner]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "scac_or_iata"]


class ShipmentViewSet(viewsets.ModelViewSet):
    """
    Core integration endpoint. Transporters and partner gateways create
    and update shipments here; Callum fans status changes back out via
    the events sub-resource. Every mode (air/sea/land) is served by the
    same endpoint — filter with ?mode=AIR|SEA|LAND.
    """

    queryset = Shipment.objects.select_related(
        "origin_gateway", "destination_gateway", "transporter"
    ).prefetch_related("events")
    serializer_class = ShipmentSerializer
    permission_classes = [IsStaffOrPartner, IsOwnerPartnerOrStaff]
    filterset_class = ShipmentFilter
    search_fields = ["reference", "shipper_name", "consignee_name"]
    ordering_fields = ["created_at", "eta", "etd"]
    lookup_field = "reference"
    throttle_scope = "partner-ingest"

    def get_throttles(self):
        # Only throttle the ingest-heavy write actions; console reads stay unthrottled.
        if self.action in ("create", "update", "partial_update", "add_event"):
            return [ScopedRateThrottle()]
        return []

    @action(detail=True, methods=["get", "post"], url_path="events")
    def events(self, request, reference=None):
        """GET: full tracking timeline. POST: append a new tracking event."""
        shipment = self.get_object()

        if request.method == "GET":
            serializer = ShipmentEventSerializer(shipment.events.all(), many=True)
            return Response(serializer.data)

        serializer = ShipmentEventCreateSerializer(data=request.data, context={"shipment": shipment})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(ShipmentEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="modes")
    def modes(self, request):
        """Describes the expected mode-specific metadata contract (air/sea/land)."""
        payload = [
            {"mode": mode, "required": schema["required"], "fields": schema["fields"]}
            for mode, schema in MODE_SCHEMAS.items()
        ]
        return Response(ModeSchemaSerializer(payload, many=True).data)
