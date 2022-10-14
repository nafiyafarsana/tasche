
from django.urls import path
from .import views


urlpatterns = [
   path('place_order/',views.place_order,name='place_order'),
   path('payments/',views.payments,name='payments'),
   path('success/',views.success,name='success'),
   path('payment_status/',views.payment_status,name='payment_status'),
   path('payment_failure/',views.payment_failure,name='payment_failure'),
]