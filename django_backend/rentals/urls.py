from django.urls import path
from .views import (
    PropertyList, BookingListCreate, PaymentCreate,
    TenantListCreate, UserRegistrationView, payment_callback, CustomTokenObtainPairView
)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('properties/', PropertyList.as_view(), name='properties-list'),
    path('bookings/', BookingListCreate.as_view(), name='bookings-list-create'),
    path('payments/', PaymentCreate.as_view(), name='payments-create'),
    path('tenants/', TenantListCreate.as_view(), name='tenant-list-create'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', obtain_auth_token, name='api_login'),

    # NEW: Node → Django payment callback
    path('payments/callback/', payment_callback, name='payment-callback'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]