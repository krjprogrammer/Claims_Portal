from django.contrib import admin
from .models import PortalUser, PortalRoles, PortalPages, EmailOTP

admin.site.register(PortalUser)
admin.site.register(PortalRoles)
admin.site.register(PortalPages)
admin.site.register(EmailOTP)

