from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Partner
from apps.gateways.models import Gateway
from apps.transporters.models import Transporter
from apps.shipments.models import Shipment


class Command(BaseCommand):
    help = "Seeds Callum with demo gateways, transporters and one shipment per mode."

    def handle(self, *args, **options):
        now = timezone.now()

        hub, _ = Gateway.objects.update_or_create(
            code="CALLUM-HUB",
            defaults=dict(name="Callum Hub", kind=Gateway.GatewayKind.HUB, country="US", city="Miami"),
        )
        mex, _ = Gateway.objects.update_or_create(
            code="MEX-GDL-01",
            defaults=dict(name="Guadalajara Partner Gateway", kind=Gateway.GatewayKind.PARTNER, country="MX", city="Guadalajara"),
        )
        deu, _ = Gateway.objects.update_or_create(
            code="DEU-HAM-01",
            defaults=dict(name="Hamburg Partner Gateway", kind=Gateway.GatewayKind.PARTNER, country="DE", city="Hamburg"),
        )

        air_partner = Partner.objects.filter(name="SkyLift Air Cargo").first() or Partner.objects.create(
            name="SkyLift Air Cargo", partner_type=Partner.PartnerType.TRANSPORTER
        )
        sea_partner = Partner.objects.filter(name="BlueWave Ocean Lines").first() or Partner.objects.create(
            name="BlueWave Ocean Lines", partner_type=Partner.PartnerType.TRANSPORTER
        )
        land_partner = Partner.objects.filter(name="RoadRunner Logistics").first() or Partner.objects.create(
            name="RoadRunner Logistics", partner_type=Partner.PartnerType.TRANSPORTER
        )

        air_t, _ = Transporter.objects.update_or_create(
            code="SKYLIFT", defaults=dict(name="SkyLift Air Cargo", modes="AIR", scac_or_iata="SLA", partner=air_partner)
        )
        sea_t, _ = Transporter.objects.update_or_create(
            code="BLUEWAVE", defaults=dict(name="BlueWave Ocean Lines", modes="SEA", scac_or_iata="BLWV", partner=sea_partner)
        )
        land_t, _ = Transporter.objects.update_or_create(
            code="ROADRUNNER", defaults=dict(name="RoadRunner Logistics", modes="LAND", partner=land_partner)
        )

        Shipment.objects.get_or_create(
            transporter=air_t,
            mode=Shipment.Mode.AIR,
            origin_gateway=hub,
            destination_gateway=deu,
            shipper_name="Acme Exports",
            consignee_name="Nordic Retail GmbH",
            defaults=dict(
                weight_kg=420, pieces=12,
                metadata={"awb_number": "020-12345670", "flight_number": "SL204", "origin_airport": "MIA", "destination_airport": "HAM"},
                etd=now + timedelta(hours=6), eta=now + timedelta(hours=18),
            ),
        )
        Shipment.objects.get_or_create(
            transporter=sea_t,
            mode=Shipment.Mode.SEA,
            origin_gateway=hub,
            destination_gateway=deu,
            shipper_name="Acme Exports",
            consignee_name="Nordic Retail GmbH",
            defaults=dict(
                weight_kg=18500, volume_m3=32, pieces=1,
                metadata={"bl_number": "BLWVMIA0093", "vessel_name": "MV Meridian", "container_number": "BLWU1234567", "container_type": "40HC"},
                etd=now + timedelta(days=1), eta=now + timedelta(days=21),
            ),
        )
        Shipment.objects.get_or_create(
            transporter=land_t,
            mode=Shipment.Mode.LAND,
            origin_gateway=hub,
            destination_gateway=mex,
            shipper_name="Acme Exports",
            consignee_name="Distribuidora Occidente",
            defaults=dict(
                weight_kg=9200, pieces=40,
                metadata={"waybill_number": "RR-88213", "plate_number": "MIA-2291", "route": "I-95 S / Border crossing Laredo"},
                etd=now + timedelta(hours=2), eta=now + timedelta(hours=30),
            ),
        )

        self.stdout.write(self.style.SUCCESS("Seeded gateways, transporters and one shipment per mode (AIR/SEA/LAND)."))
