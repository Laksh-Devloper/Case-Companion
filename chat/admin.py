from django.contrib import admin
from .models import ChatMessage

# Register ChatMessage with a basic admin interface
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'bot_response', 'timestamp')  # Fields to display in the list view
    list_filter = ('user', 'timestamp')  # Add filters for user and timestamp
    search_fields = ('message', 'bot_response')  # Enable search by message and bot_response

# Register your models here.
