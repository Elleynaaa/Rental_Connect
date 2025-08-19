from rest_framework import serializers
from .models import Property, Booking, Payment, Tenant, UserProfile
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role"]


class PropertySerializer(serializers.ModelSerializer):
    landlord = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Property
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': False, 'allow_blank': True},
            'price_per_month': {'required': True},
            'image_url': {'required': False, 'allow_blank': True},
            'approved': {'read_only': True},
        }


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
class BookingDashboardSerializer(serializers.ModelSerializer):
    tenant_email = serializers.CharField(source='tenant.email', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'tenant_email', 'property_name', 'booking_date', 'status', 'time_slot', 'room_type']



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
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default="tenant")
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
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'phone_number', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Pop extra fields that are not in User model
        phone_number = validated_data.pop('phone_number', None)
        role = validated_data.pop('role', 'tenant')
        password = validated_data.pop('password')

        # Create user
        user = User(**validated_data)
        user.set_password(password)

        # Temporarily attach role for signals to pick up
        user.role = role
        user.save()  # Signals will handle UserProfile & Tenant creation

        # Update Tenant's phone number if role is tenant
        if role == "tenant" and phone_number:
            tenant = getattr(user, 'tenant', None)
            if tenant:
                tenant.phone_number = phone_number
                tenant.save()

        return user