from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user else "No User"

class Booking(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    booking_date = models.DateField()
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Booking for {self.tenant} - {self.property}"

class Payment(models.Model):
    # existing fields
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=50, default="Pending")  # e.g. Pending, Completed

    # new fields to capture M-Pesa info
    mpesa_receipt = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    result_code = models.IntegerField(blank=True, null=True)
    result_desc = models.TextField(blank=True, null=True)
    transaction_time = models.DateTimeField(blank=True, null=True)
    raw_callback = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.amount} for {self.booking or 'No booking'}"

