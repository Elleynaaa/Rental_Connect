from rest_framework import serializers
from .models import Property, Booking, Payment, Tenant
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    tenant_email = serializers.EmailField(source='booking.tenant.user.email', read_only=True)
    booking_status = serializers.CharField(source='booking.status', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'

class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        phone = validated_data.pop('phone_number')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        tenant, created = Tenant.objects.update_or_create(
            user=user,
            defaults={'phone_number': phone}
        )
        return user