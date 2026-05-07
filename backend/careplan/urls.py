from django.urls import path
from . import views

urlpatterns = [
    path('api/orders/', views.create_order, name='create_order'),
    path('api/orders/<str:order_id>/', views.get_order, name='get_order'),
    path('api/careplan/<int:careplan_id>/status/', views.get_careplan_status, name='get_careplan_status'),
]