from django.contrib import admin
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model.
    """
    list_display = ['message_id', 'sender', 'recipient', 'message_preview', 'sent_at']
    list_filter = ['sent_at', 'sender', 'recipient']
    search_fields = ['sender__username', 'recipient__username', 'message_body']
    readonly_fields = ['message_id', 'sent_at']
    date_hierarchy = 'sent_at'
    ordering = ['-sent_at']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'sender', 'recipient', 'message_body')
        }),
        ('Timestamp', {
            'fields': ('sent_at',)
        }),
    )

    def message_preview(self, obj):
        """Display first 50 characters of message body."""
        return obj.message_body[:50] + '...' if len(obj.message_body) > 50 else obj.message_body
    
    message_preview.short_description = 'Message Preview'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = ['notification_id', 'user', 'notification_type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at', 'user']
    search_fields = ['user__username', 'content']
    readonly_fields = ['notification_id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('notification_id', 'user', 'notification_type', 'content')
        }),
        ('Related Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']

    def content_preview(self, obj):
        """Display first 50 characters of content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    
    mark_as_read.short_description = 'Mark selected notifications as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    
    mark_as_unread.short_description = 'Mark selected notifications as unread'