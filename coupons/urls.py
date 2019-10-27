from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("order/<str:coupon_type>", views.order, name="order"),
    path("cancel", views.order_cancel, name="order_cancel"),
    path("callback", views.order_callback, name="order_callback"),
    path("accept/<int:order_id>", views.order_accept, name="order_accept"),
    path("coupon/<str:coupon_id>", views.coupon, name="coupon"),
    path("coupon/<str:coupon_id>/qr", views.coupon_qr, name="coupon_qr"),
    path("admin/check/<str:coupon_id>", views.coupon_check, name="coupon_check"),
    path(
        "admin/check/<str:coupon_id>/actions",
        views.coupon_actions,
        name="coupon_actions",
    ),
    path("admin/list", views.coupon_list, name="coupon_list"),
]
