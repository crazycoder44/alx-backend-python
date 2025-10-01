from django.contrib import admin
from .models import Message, Notification, MessageHistory


class MessageHistoryInline(admin.TabularInline):
    """
    Inline admin for displaying message edit history.
    """
    model = MessageHistory
    extra = 0
    readonly_fields = ['history_id', 'old_content', 'edited_at', 'edited_by']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Prevent manual addition of history entries."""
        return False



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
    inlines = [MessageHistoryInline]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'sender', 'receiver', 'content')
        }),
        ('Timestamp & Edit Info', {
            'fields': ('timestamp', 'edited', 'last_edited_at')
        }),
    )

    def content_preview(self, obj):
        """Display first 50 characters of content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for MessageHistory model.
    """
    list_display = ['history_id', 'message', 'old_content_preview', 'edited_at', 'edited_by']
    list_filter = ['edited_at', 'edited_by']
    search_fields = ['message__message_id', 'old_content', 'edited_by__username']
    readonly_fields = ['history_id', 'message', 'old_content', 'edited_at', 'edited_by']
    date_hierarchy = 'edited_at'
    ordering = ['-edited_at']
    
    fieldsets = (
        ('History Information', {
            'fields': ('history_id', 'message', 'old_content')
        }),
        ('Edit Details', {
            'fields': ('edited_at', 'edited_by')
        }),
    )

    def old_content_preview(self, obj):
        """Display first 50 characters of old content."""
        return obj.old_content[:50] + '...' if len(obj.old_content) > 50 else obj.old_content
    
    old_content_preview.short_description = 'Old Content Preview'

    def has_add_permission(self, request):
        """Prevent manual addition of history entries."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of history entries."""
        return False


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