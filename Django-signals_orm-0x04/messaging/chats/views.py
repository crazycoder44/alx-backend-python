from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from messaging.models import Message, Notification
import logging

logger = logging.getLogger(__name__)


@cache_page(60)  # Cache for 60 seconds
def conversation_list_view(request, conversation_id):
    """
    View to display a list of messages in a conversation.
    This view is cached for 60 seconds using cache_page decorator.
    
    Args:
        request: HTTP request object
        conversation_id: UUID of the conversation/message thread
    
    Returns:
        Rendered template with conversation messages
    """
    logger.info(f"Fetching conversation {conversation_id} - Cache Miss")
    
    # Get the message (root or any message in thread)
    message = get_object_or_404(Message, message_id=conversation_id)
    
    # Get the root message of the thread
    root_message = message.get_thread_root()
    
    # Get all messages in the conversation with optimized queries
    conversation_messages = Message.objects.filter(
        Q(message_id=root_message.message_id) |
        Q(parent_message=root_message) |
        Q(parent_message__parent_message=root_message) |
        Q(parent_message__parent_message__parent_message=root_message)
    ).select_related(
        'sender', 'receiver', 'parent_message'
    ).prefetch_related('replies').order_by('timestamp')
    
    # Get participants
    participants = message.get_conversation_participants()
    
    context = {
        'root_message': root_message,
        'conversation_messages': conversation_messages,
        'participants': participants,
        'message_count': conversation_messages.count(),
        'cached_view': True,
    }
    
    return render(request, 'chats/conversation_list.html', context)


@login_required
@cache_page(60)  # Cache for 60 seconds
def user_conversations_cached(request):
    """
    View to display all conversations for the logged-in user.
    Cached for 60 seconds to improve performance.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with user's conversations
    """
    user = request.user
    logger.info(f"Fetching conversations for user {user.username} - Cache Miss")
    
    # Get all root messages where user is sender or receiver
    root_messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user),
        parent_message__isnull=True
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch('replies',
                 queryset=Message.objects.select_related('sender', 'receiver'))
    ).order_by('-timestamp')
    
    # Get unread count
    unread_count = Message.unread.unread_count_for_user(user)
    
    context = {
        'conversations': root_messages,
        'unread_count': unread_count,
        'cached_view': True,
    }
    
    return render(request, 'chats/user_conversations.html', context)


@cache_page(60, key_prefix='message_detail')  # Cache with custom key prefix
def message_detail_cached(request, message_id):
    """
    Cached view for message detail page.
    Uses custom key prefix for cache organization.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message
    
    Returns:
        Rendered template with message details
    """
    logger.info(f"Fetching message detail {message_id} - Cache Miss")
    
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver', 'parent_message'),
        message_id=message_id
    )
    
    # Get replies
    replies = message.replies.select_related('sender', 'receiver').order_by('timestamp')
    
    context = {
        'message': message,
        'replies': replies,
        'reply_count': replies.count(),
        'cached_view': True,
    }
    
    return render(request, 'chats/message_detail.html', context)


@login_required
def invalidate_conversation_cache(request, conversation_id):
    """
    View to manually invalidate cache for a specific conversation.
    Useful when new messages are posted.
    
    Args:
        request: HTTP request object
        conversation_id: UUID of the conversation
    
    Returns:
        JSON response with status
    """
    from django.core.cache.utils import make_template_fragment_key
    from django.utils.cache import get_cache_key
    
    # Clear view cache
    cache_key = f'views.decorators.cache.cache_page.conversation_list_view.{conversation_id}'
    cache.delete(cache_key)
    
    logger.info(f"Cache invalidated for conversation {conversation_id}")
    
    return JsonResponse({
        'status': 'success',
        'message': f'Cache cleared for conversation {conversation_id}'
    })


@login_required
def clear_user_cache(request):
    """
    View to clear all cache for the current user.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with status
    """
    user = request.user
    
    # Clear specific cache entries
    cache.delete(f'user_conversations_{user.id}')
    cache.delete(f'unread_count_{user.id}')
    
    logger.info(f"Cache cleared for user {user.username}")
    
    return JsonResponse({
        'status': 'success',
        'message': f'Cache cleared for user {user.username}'
    })


def cached_stats_view(request):
    """
    View to display cached statistics.
    Uses low-level cache API for fine-grained control.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with cached stats
    """
    # Try to get from cache first
    stats = cache.get('message_stats')
    
    if stats is None:
        logger.info("Calculating message stats - Cache Miss")
        
        # Calculate stats (expensive operation)
        total_messages = Message.objects.count()
        total_conversations = Message.objects.filter(parent_message__isnull=True).count()
        total_unread = Message.objects.filter(read=False).count()
        
        stats = {
            'total_messages': total_messages,
            'total_conversations': total_conversations,
            'total_unread': total_unread,
            'cached': False,
        }
        
        # Store in cache for 5 minutes
        cache.set('message_stats', stats, 300)
    else:
        logger.info("Message stats retrieved from cache - Cache Hit")
        stats['cached'] = True
    
    return JsonResponse(stats)


@cache_page(60, cache='default', key_prefix='inbox')
def inbox_cached_view(request, user_id):
    """
    Cached inbox view for a specific user.
    Demonstrates cache_page with multiple parameters.
    
    Args:
        request: HTTP request object
        user_id: ID of the user
    
    Returns:
        Rendered template with inbox
    """
    from django.contrib.auth.models import User
    
    user = get_object_or_404(User, id=user_id)
    logger.info(f"Fetching inbox for user {user.username} - Cache Miss")
    
    # Get received messages with optimization
    received_messages = Message.objects.filter(
        receiver=user
    ).select_related('sender').only(
        'message_id',
        'sender__username',
        'content',
        'timestamp',
        'read',
        'edited'
    ).order_by('-timestamp')[:50]
    
    # Get unread count
    unread_count = Message.unread.unread_count_for_user(user)
    
    context = {
        'user': user,
        'received_messages': received_messages,
        'unread_count': unread_count,
        'cached_view': True,
    }
    
    return render(request, 'chats/inbox.html', context)


# Non-cached version for comparison
def conversation_list_view_uncached(request, conversation_id):
    """
    Non-cached version of conversation list view for performance comparison.
    
    Args:
        request: HTTP request object
        conversation_id: UUID of the conversation
    
    Returns:
        Rendered template with conversation messages
    """
    logger.info(f"Fetching conversation {conversation_id} - No Cache")
    
    message = get_object_or_404(Message, message_id=conversation_id)
    root_message = message.get_thread_root()
    
    conversation_messages = Message.objects.filter(
        Q(message_id=root_message.message_id) |
        Q(parent_message=root_message) |
        Q(parent_message__parent_message=root_message)
    ).select_related(
        'sender', 'receiver', 'parent_message'
    ).prefetch_related('replies').order_by('timestamp')
    
    participants = message.get_conversation_participants()
    
    context = {
        'root_message': root_message,
        'conversation_messages': conversation_messages,
        'participants': participants,
        'message_count': conversation_messages.count(),
        'cached_view': False,
    }
    
    return render(request, 'chats/conversation_list.html', context)


def cache_info_view(request):
    """
    View to display cache information and statistics.
    Useful for debugging and monitoring.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with cache info
    """
    from django.conf import settings
    
    cache_config = settings.CACHES['default']
    
    info = {
        'backend': cache_config['BACKEND'],
        'location': cache_config.get('LOCATION', 'N/A'),
        'timeout': cache_config.get('TIMEOUT', 'N/A'),
        'max_entries': cache_config.get('OPTIONS', {}).get('MAX_ENTRIES', 'N/A'),
        'middleware_seconds': getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 'N/A'),
        'key_prefix': getattr(settings, 'CACHE_MIDDLEWARE_KEY_PREFIX', 'N/A'),
    }
    
    return JsonResponse(info)