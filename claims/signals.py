from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PortalPages, PortalRoles, PortalUser
from utils import send_mail


@receiver(post_save, sender=PortalPages)
def add_page_to_superadmin(sender, instance, created, **kwargs):
    if created:
        superadmin_roles = PortalRoles.objects.filter(name="superadmin")
        for role in superadmin_roles:
            role.access_pages.add(instance)


@receiver(post_save, sender=PortalUser)
def send_welcome_email(sender, instance, created, **kwargs):
    if not created:
        return

    temp_password = getattr(instance, 'temp_password', None)
    if not temp_password or not instance.email:
        return

    role = instance.role.name.title() if instance.role else "N/A"

    subject = "Welcome to the Claims Portal"
    message = (
        f"Dear {instance.username},\n\n"
        f"Your account has been successfully created in the Claims Portal.\n\n"
        f"Account Details:\n"
        f"  - Role              : {role}\n"
        f"  - Registered Email  : {instance.email}\n"
        f"  - Login Username    : {instance.username}\n"
        f"  - Login Password    : {temp_password}\n\n"
        f"Login Instructions:\n"
        f"  1. Use the above credentials to log in to the Claims Portal.\n"
        f"  2. For security reasons, please change your username and password immediately after your first login.\n"
        f"  3. You are required to activate Two-Factor Authentication (2FA) on your first login to secure your account.\n\n"
        f"Thank you and welcome aboard!\n\n"
        f"Best regards,\n"
        f"Claims Portal Team"
    )

    send_mail(subject=subject, message=message, recipients=instance.email)
    instance.temp_password = None
    instance.save(update_fields=["temp_password"])
