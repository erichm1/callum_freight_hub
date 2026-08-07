from rest_framework.routers import DefaultRouter

from apps.shipments.api.views import GatewayViewSet, TransporterViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("gateways", GatewayViewSet, basename="gateway")
router.register("transporters", TransporterViewSet, basename="transporter")
router.register("shipments", ShipmentViewSet, basename="shipment")

urlpatterns = router.urls
