from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Tenant, UserProfile

@receiver(post_save, sender=User)
def create_user_related(sender, instance, created, **kwargs):
    if created:
        # Default role is tenant, or get it from a temporary attribute set during registration
        role = getattr(instance, 'role', 'tenant')

        # Create UserProfile
        UserProfile.objects.create(user=instance, role=role)

        # Create Tenant only if role is tenant
        if role == 'tenant':
            Tenant.objects.create(user=instance)