from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("order/<str:coupon_type>", views.order, name="order"),
    path("cancel", views.cancel, name="cancel"),
]
