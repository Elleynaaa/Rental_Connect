from rest_framework import generics, filters, permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Property, Booking, Payment, Tenant, UserProfile
from .serializers import (
    PropertySerializer, BookingSerializer, PaymentSerializer,
    TenantSerializer, UserRegistrationSerializer, BookingDashboardSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from .tokens import CustomTokenObtainPairSerializer
from .permissions import IsLandlord, IsAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# Anyone can list properties (only approved ones)
class PropertyList(generics.ListAPIView):
    queryset = Property.objects.filter(approved=True)
    serializer_class = PropertySerializer


# Landlord can create/list their properties
class LandlordPropertyListCreate(generics.ListCreateAPIView):
    serializer_class = PropertySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsLandlord]

    def get_queryset(self):
        return Property.objects.filter(landlord=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(landlord=self.request.user, approved=False)
        except Exception:
            print("Serializer errors:", serializer.errors)
            raise


# Admin can approve properties
class ApprovePropertyView(generics.UpdateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def perform_update(self, serializer):
        serializer.save(approved=True)

    # Allow POST request to trigger update
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


# Booking views
class BookingListCreate(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class LandlordBookingList(generics.ListAPIView):
    serializer_class = BookingDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsLandlord]

    def get_queryset(self):
        return Booking.objects.filter(property__landlord=self.request.user)


# Admin: all bookings
class AdminBookingList(generics.ListAPIView):
    serializer_class = BookingDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Booking.objects.all()


# Payments
class PaymentCreate(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


# Tenants
class TenantListCreate(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email']


# User registration
class UserRegistrationView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserRegistrationSerializer


# M-Pesa payment callback
@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        booking_id = data.get("booking_id")
        email = data.get("email")
        result_code = data.get("result_code")
        result_desc = data.get("result_desc")
        amount = data.get("amount")
        mpesa_receipt = data.get("mpesa_receipt")
        phone_number = data.get("phone_number")
        transaction_date = data.get("transaction_date")
        raw_callback = data.get("raw_callback")

        dt_parsed = None
        if transaction_date:
            try:
                dt_parsed = datetime.strptime(str(transaction_date), "%Y%m%d%H%M%S")
            except Exception:
                dt_parsed = None

        try:
            booking = Booking.objects.get(id=booking_id, tenant__user__email=email)
        except Booking.DoesNotExist:
            return JsonResponse({"error": "Booking not found"}, status=404)

        status = "Paid" if result_code == 0 else "Failed"

        if status == "Paid":
            booking.status = "Paid"
            booking.save()

        Payment.objects.create(
            booking=booking,
            amount=amount or 0,
            payment_status=status,
            mpesa_receipt=mpesa_receipt,
            phone_number=phone_number,
            result_code=result_code,
            result_desc=result_desc,
            transaction_time=dt_parsed,
            raw_callback=raw_callback,
        )

        return JsonResponse({"message": f"Payment processed, Booking status: {status}"}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)