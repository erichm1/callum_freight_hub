from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from apps.shipments.models import Shipment
from apps.gateways.models import Gateway
from apps.transporters.models import Transporter


class CallumLoginView(LoginView):
    template_name = "callum/login.html"


class CallumLogoutView(LogoutView):
    next_page = "dashboard:login"


@login_required
def home(request):
    shipments = Shipment.objects.all()

    mode_counts = {
        row["mode"]: row["count"]
        for row in shipments.values("mode").annotate(count=Count("id"))
    }
    status_counts = {
        row["status"]: row["count"]
        for row in shipments.values("status").annotate(count=Count("id"))
    }

    active_statuses = [
        Shipment.Status.PICKED_UP,
        Shipment.Status.IN_TRANSIT,
        Shipment.Status.AT_GATEWAY,
        Shipment.Status.OUT_FOR_DELIVERY,
    ]

    context = {
        "mode_counts": {
            "AIR": mode_counts.get("AIR", 0),
            "SEA": mode_counts.get("SEA", 0),
            "LAND": mode_counts.get("LAND", 0),
        },
        "total_shipments": shipments.count(),
        "active_count": shipments.filter(status__in=active_statuses).count(),
        "exception_count": status_counts.get(Shipment.Status.EXCEPTION, 0),
        "delivered_count": status_counts.get(Shipment.Status.DELIVERED, 0),
        "gateway_count": Gateway.objects.filter(is_active=True).count(),
        "transporter_count": Transporter.objects.filter(is_active=True).count(),
        "recent_shipments": shipments.select_related(
            "origin_gateway", "destination_gateway", "transporter"
        ).order_by("-created_at")[:8],
        "now": timezone.now(),
    }
    return render(request, "callum/home.html", context)


@login_required
def shipment_list(request):
    shipments = Shipment.objects.select_related(
        "origin_gateway", "destination_gateway", "transporter"
    ).order_by("-created_at")

    mode = request.GET.get("mode")
    status_ = request.GET.get("status")
    query = request.GET.get("q")

    if mode:
        shipments = shipments.filter(mode=mode)
    if status_:
        shipments = shipments.filter(status=status_)
    if query:
        shipments = shipments.filter(
            Q(reference__icontains=query)
            | Q(shipper_name__icontains=query)
            | Q(consignee_name__icontains=query)
        )

    context = {
        "shipments": shipments[:200],
        "mode_choices": Shipment.Mode.choices,
        "status_choices": Shipment.Status.choices,
        "selected_mode": mode or "",
        "selected_status": status_ or "",
        "query": query or "",
    }
    return render(request, "callum/shipment_list.html", context)


@login_required
def shipment_detail(request, reference):
    shipment = get_object_or_404(
        Shipment.objects.select_related("origin_gateway", "destination_gateway", "transporter"),
        reference=reference,
    )
    timeline = shipment.events.all()
    context = {"shipment": shipment, "timeline": timeline}
    return render(request, "callum/shipment_detail.html", context)
