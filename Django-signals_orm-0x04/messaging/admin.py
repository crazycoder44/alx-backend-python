from django.contrib import admin
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model.
    """
    list_display = ['message_id', 'sender', 'receiver', 'content_preview', 'timestamp']
    list_filter = ['timestamp', 'sender', 'receiver']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['message_id', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'sender', 'receiver', 'content')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

    def content_preview(self, obj):
        """Display first 50 characters of content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'


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