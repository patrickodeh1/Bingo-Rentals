from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.booking_home, name='home'),
    path('product/<slug:product_slug>/', views.select_dates, name='select_dates'),
    path('details/', views.customer_details, name='customer_details'),
    path('summary/', views.order_summary, name='order_summary'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
    path('pickup/', views.schedule_pickup, name='schedule_pickup'),
    path('pickup/payment/', views.pickup_payment, name='pickup_payment'),
    path('pickup/process/', views.process_pickup, name='process_pickup'),
    path('pickup/confirmed/<uuid:booking_id>/', views.pickup_confirmed, name='pickup_confirmed'),
]
