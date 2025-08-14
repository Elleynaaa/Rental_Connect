from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Tenant

@receiver(post_save, sender=User)
def create_tenant(sender, instance, created, **kwargs):
    if created:
        Tenant.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_tenant(sender, instance, **kwargs):
    instance.tenant.save()