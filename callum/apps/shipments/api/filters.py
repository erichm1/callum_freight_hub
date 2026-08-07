import django_filters as filters

from apps.shipments.models import Shipment


class ShipmentFilter(filters.FilterSet):
    mode = filters.ChoiceFilter(choices=Shipment.Mode.choices)
    status = filters.ChoiceFilter(choices=Shipment.Status.choices)
    origin_gateway = filters.CharFilter(field_name="origin_gateway__code", lookup_expr="iexact")
    destination_gateway = filters.CharFilter(field_name="destination_gateway__code", lookup_expr="iexact")
    transporter = filters.CharFilter(field_name="transporter__code", lookup_expr="iexact")
    eta_after = filters.IsoDateTimeFilter(field_name="eta", lookup_expr="gte")
    eta_before = filters.IsoDateTimeFilter(field_name="eta", lookup_expr="lte")

    class Meta:
        model = Shipment
        fields = ["mode", "status", "origin_gateway", "destination_gateway", "transporter"]
