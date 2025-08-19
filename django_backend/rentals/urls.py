from django.urls import path
from .views import (
    PropertyList, BookingListCreate, PaymentCreate,
    TenantListCreate, UserRegistrationView, payment_callback,
    CustomTokenObtainPairView, LandlordPropertyListCreate, ApprovePropertyView, LandlordBookingList, AdminBookingList
)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('properties/', PropertyList.as_view(), name='properties-list'),
    path('landlord/properties/', LandlordPropertyListCreate.as_view(), name='landlord-properties'),
    path('admin/properties/<int:pk>/approve/', ApprovePropertyView.as_view(), name='approve-property'),

    path('bookings/', BookingListCreate.as_view(), name='bookings-list-create'),
    path('payments/', PaymentCreate.as_view(), name='payments-create'),
    path('tenants/', TenantListCreate.as_view(), name='tenant-list-create'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', obtain_auth_token, name='api_login'),

    path('payments/callback/', payment_callback, name='payment-callback'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('landlord/bookings/', LandlordBookingList.as_view(), name='landlord-bookings'),
    path('admin/bookings/', AdminBookingList.as_view(), name='admin-bookings'),
]