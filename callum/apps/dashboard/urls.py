from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("shipments/", views.shipment_list, name="shipment_list"),
    path("shipments/<str:reference>/", views.shipment_detail, name="shipment_detail"),
    path("login/", views.CallumLoginView.as_view(), name="login"),
    path("logout/", views.CallumLogoutView.as_view(), name="logout"),
]
