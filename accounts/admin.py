# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Contact, EmailVerification

# Define a custom admin class for CustomUser
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list view
    list_display = ('email', 'username', 'phone_number', 'email_verified', 'date_joined', 'is_staff')
    # Fields to filter by in the admin
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified')
    # Fields to search by in the admin
    search_fields = ('email', 'username')
    # Customize the fieldsets for the edit view
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('phone_number', 'email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        # CHANGED: Removed date_joined from fieldsets
    )
    # CHANGED: Added readonly_fields for date_joined
    readonly_fields = ('date_joined',)
    # Customize the add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone_number', 'password1', 'password2'),
        }),
    )
    # Order the fields
    ordering = ('email',)
    actions = ['delete_selected']  # Retained: Enable delete action

# Define a custom admin class for Contact
class ContactAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    list_display = ('user', 'email', 'contact_number', 'message', 'created_at')
    # Fields to filter by in the admin
    list_filter = ('created_at',)
    # Fields to search by in the admin
    search_fields = ('email', 'contact_number', 'message')
    # Customize the fieldsets for the edit view
    fieldsets = (
        (None, {'fields': ('user', 'email', 'contact_number', 'message')}),
        ('Metadata', {'fields': ('created_at',)}),
    )
    # Make created_at read-only
    readonly_fields = ('created_at',)
    # Order the fields
    ordering = ('-created_at',)

# Define a custom admin class for EmailVerification
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'token', 'created_at', 'expires_at', 'is_verified')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at', 'token')
    ordering = ('-created_at',)

# Register CustomUser with the custom admin class
admin.site.register(CustomUser, CustomUserAdmin)
# Register Contact with the custom admin class
admin.site.register(Contact, ContactAdmin)
# Register EmailVerification
admin.site.register(EmailVerification, EmailVerificationAdmin)