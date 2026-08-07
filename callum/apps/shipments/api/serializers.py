from rest_framework import serializers

from apps.gateways.models import Gateway
from apps.transporters.models import Transporter
from apps.shipments.models import Shipment, ShipmentEvent
from apps.shipments.mode_schemas import validate_metadata, MODE_SCHEMAS


class GatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = [
            "id", "code", "name", "kind", "country", "city", "timezone",
            "supports_air", "supports_sea", "supports_land", "is_active",
        ]


class TransporterSerializer(serializers.ModelSerializer):
    modes = serializers.SerializerMethodField()

    class Meta:
        model = Transporter
        fields = [
            "id", "code", "name", "modes", "scac_or_iata",
            "coverage_countries", "is_active",
        ]

    def get_modes(self, obj):
        return obj.mode_list()


class ShipmentEventSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ShipmentEvent
        fields = ["id", "status", "status_display", "location", "description", "source", "created_at"]
        read_only_fields = ["id", "created_at"]


class ShipmentSerializer(serializers.ModelSerializer):
    """Full read/write serializer used by the shipments viewset."""

    mode_display = serializers.CharField(source="get_mode_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    origin_gateway_code = serializers.CharField(source="origin_gateway.code", read_only=True)
    destination_gateway_code = serializers.CharField(source="destination_gateway.code", read_only=True)
    transporter_name = serializers.CharField(source="transporter.name", read_only=True)
    latest_event = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = [
            "id", "reference", "mode", "mode_display", "status", "status_display",
            "origin_gateway", "origin_gateway_code",
            "destination_gateway", "destination_gateway_code",
            "transporter", "transporter_name", "submitted_by",
            "shipper_name", "consignee_name", "description_of_goods",
            "weight_kg", "volume_m3", "pieces", "metadata",
            "etd", "eta", "actual_departure", "actual_arrival",
            "latest_event", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "reference", "submitted_by", "created_at", "updated_at"]

    def get_latest_event(self, obj):
        event = obj.events.first()
        return ShipmentEventSerializer(event).data if event else None

    def validate(self, attrs):
        mode = attrs.get("mode", getattr(self.instance, "mode", None))
        metadata = attrs.get("metadata", getattr(self.instance, "metadata", {}) or {})
        errors = validate_metadata(mode, metadata)
        if errors:
            raise serializers.ValidationError({"metadata": errors})

        origin = attrs.get("origin_gateway", getattr(self.instance, "origin_gateway", None))
        destination = attrs.get("destination_gateway", getattr(self.instance, "destination_gateway", None))
        transporter = attrs.get("transporter", getattr(self.instance, "transporter", None))

        if origin and not origin.supports_mode(mode):
            raise serializers.ValidationError({"origin_gateway": f"{origin.code} does not support {mode}."})
        if destination and not destination.supports_mode(mode):
            raise serializers.ValidationError({"destination_gateway": f"{destination.code} does not support {mode}."})
        if origin and destination and origin_id_eq(origin, destination):
            raise serializers.ValidationError({"destination_gateway": "Origin and destination must differ."})
        if transporter and not transporter.operates_mode(mode):
            raise serializers.ValidationError({"transporter": f"{transporter.name} does not operate {mode}."})

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        partner = getattr(request, "auth", None)
        if partner is not None and hasattr(partner, "partner_type"):
            validated_data["submitted_by"] = partner
        shipment = super().create(validated_data)
        shipment.events.create(
            status=shipment.status,
            description="Shipment created",
            source=_event_source_for(partner),
        )
        return shipment


def origin_id_eq(a, b):
    return a.pk == b.pk


def _event_source_for(partner):
    if partner is None:
        return ShipmentEvent.Source.INTERNAL
    if getattr(partner, "partner_type", "") == "TRANSPORTER":
        return ShipmentEvent.Source.TRANSPORTER
    if getattr(partner, "partner_type", "") == "GATEWAY":
        return ShipmentEvent.Source.GATEWAY
    return ShipmentEvent.Source.INTERNAL


class ShipmentEventCreateSerializer(serializers.ModelSerializer):
    """Used by the /shipments/{id}/events/ action to append a tracking event."""

    class Meta:
        model = ShipmentEvent
        fields = ["status", "location", "description", "source"]

    def create(self, validated_data):
        shipment = self.context["shipment"]
        event = ShipmentEvent.objects.create(shipment=shipment, **validated_data)
        shipment.status = validated_data["status"]
        shipment.save(update_fields=["status", "updated_at"])
        return event


class ModeSchemaSerializer(serializers.Serializer):
    """Read-only helper serializer describing the expected metadata shape per mode."""

    mode = serializers.CharField()
    required = serializers.ListField(child=serializers.CharField())
    fields = serializers.DictField(child=serializers.CharField())
