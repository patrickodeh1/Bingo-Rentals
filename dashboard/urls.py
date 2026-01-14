from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('orders/', views.manage_orders, name='manage_orders'),
    path('orders/<uuid:booking_id>/', views.order_detail, name='order_detail'),
    path('inventory/', views.manage_inventory, name='manage_inventory'),
    path('pricing/', views.pricing_settings, name='pricing_settings'),
    path('blackouts/', views.manage_blackouts, name='manage_blackouts'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
