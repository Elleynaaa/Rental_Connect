from rest_framework import generics, filters
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime

from .models import Property, Booking, Payment, Tenant
from .serializers import (
    PropertySerializer, BookingSerializer, PaymentSerializer,
    TenantSerializer, UserRegistrationSerializer
)

from rest_framework_simplejwt.views import TokenObtainPairView
from .tokens import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
class PropertyList(generics.ListAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

class BookingListCreate(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

class PaymentCreate(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class TenantListCreate(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email']

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer


@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    """
    Receives forwarded M-Pesa callback data from Node and persists it in Payment,
    and updates the corresponding Booking status.
    Expected JSON:
    {
      "booking_id": int,
      "email": str,
      "result_code": int,
      "result_desc": str,
      "amount": number,
      "mpesa_receipt": str,
      "phone_number": str,
      "transaction_date": "YYYYMMDDHHMMSS",
      "raw_callback": {...original Safaricom JSON...}
    }
    """
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

        # Parse Safaricom timestamp
        dt_parsed = None
        if transaction_date:
            try:
                dt_parsed = datetime.strptime(str(transaction_date), "%Y%m%d%H%M%S")
            except Exception:
                dt_parsed = None

        # Lookup Booking via booking_id and tenant email
        try:
            booking = Booking.objects.get(id=booking_id, tenant__user__email=email)
        except Booking.DoesNotExist:
            return JsonResponse({"error": "Booking not found"}, status=404)

        # Determine status
        status = "Paid" if result_code == 0 else "Failed"

        # Update booking status if payment successful
        if status == "Paid":
            booking.status = "Paid"
            booking.save()

        # Save Payment record linked to the booking
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