from django.urls import path
from .views import PropertyList, BookingListCreate, PaymentCreate, TenantListCreate, UserRegistrationView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('properties/', PropertyList.as_view(), name='properties-list'),
    path('bookings/', BookingListCreate.as_view(), name='bookings-list-create'),
    path('payments/', PaymentCreate.as_view(), name='payments-create'),
    path('tenants/', TenantListCreate.as_view(), name='tenant-list-create'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', obtain_auth_token, name='api_login'),
]