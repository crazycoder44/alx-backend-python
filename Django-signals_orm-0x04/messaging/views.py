from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Message, MessageHistory


@login_required
def message_detail(request, message_id):
    """
    View to display a message with its edit history.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message to display
    
    Returns:
        Rendered template with message and history
    """
    message = get_object_or_404(Message, message_id=message_id)
    
    # Get all history entries for this message, ordered by edit time
    history_entries = MessageHistory.objects.filter(message=message).order_by('-edited_at')
    
    context = {
        'message': message,
        'history_entries': history_entries,
        'has_history': history_entries.exists()
    }
    
    return render(request, 'messaging/message_detail.html', context)


@login_required
def message_history_json(request, message_id):
    """
    API endpoint to get message history as JSON.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message
    
    Returns:
        JSON response with message history
    """
    message = get_object_or_404(Message, message_id=message_id)
    
    # Get all history entries
    history_entries = MessageHistory.objects.filter(message=message).order_by('-edited_at')
    
    # Build response data
    history_data = []
    for entry in history_entries:
        history_data.append({
            'history_id': str(entry.history_id),
            'old_content': entry.old_content,
            'edited_at': entry.edited_at.isoformat(),
            'edited_by': entry.edited_by.username if entry.edited_by else None
        })
    
    response_data = {
        'message_id': str(message.message_id),
        'current_content': message.content,
        'edited': message.edited,
        'last_edited_at': message.last_edited_at.isoformat() if message.last_edited_at else None,
        'history': history_data
    }
    
    return JsonResponse(response_data)


@login_required
def user_messages(request):
    """
    View to display all messages for the logged-in user.
    Shows both sent and received messages with edit indicators.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with user's messages
    """
    user = request.user
    
    # Get sent and received messages
    sent_messages = Message.objects.filter(sender=user).order_by('-timestamp')
    received_messages = Message.objects.filter(receiver=user).order_by('-timestamp')
    
    context = {
        'sent_messages': sent_messages,
        'received_messages': received_messages,
    }
    
    return render(request, 'messaging/user_messages.html', context)


@login_required
def delete_user_account(request):
    """
    View to display user account deletion confirmation page.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with deletion confirmation
    """
    if request.method == 'GET':
        # Display confirmation page with user statistics
        user = request.user
        
        # Get counts of user-related data
        sent_messages_count = Message.objects.filter(sender=user).count()
        received_messages_count = Message.objects.filter(receiver=user).count()
        notifications_count = user.notifications.count()
        
        context = {
            'sent_messages_count': sent_messages_count,
            'received_messages_count': received_messages_count,
            'notifications_count': notifications_count,
            'total_messages': sent_messages_count + received_messages_count,
        }
        
        return render(request, 'messaging/delete_account.html', context)


@login_required
@require_POST
def delete_user(request):
    """
    View to handle user account deletion.
    Deletes the user account and all related data via signals.
    
    Args:
        request: HTTP request object with POST data
    
    Returns:
        Redirect to homepage after deletion
    """
    user = request.user
    username = user.username
    
    # Verify confirmation (optional security check)
    confirmation = request.POST.get('confirmation', '')
    
    if confirmation.lower() == 'delete':
        try:
            # Log out the user first
            logout(request)
            
            # Delete the user (this triggers post_delete signal)
            # The signal will automatically clean up all related data
            user.delete()
            
            # Add success message
            messages.success(
                request,
                f'Account "{username}" has been successfully deleted along with all associated data.'
            )
            
            return redirect('account_deleted')
        
        except Exception as e:
            messages.error(
                request,
                f'An error occurred while deleting your account: {str(e)}'
            )
            return redirect('delete_user_account')
    else:
        messages.error(
            request,
            'Account deletion failed. Please type "delete" to confirm.'
        )
        return redirect('delete_user_account')


def account_deleted(request):
    """
    View to display account deletion success page.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template confirming account deletion
    """
    return render(request, 'messaging/account_deleted.html')


@login_required
def user_data_summary(request):
    """
    API endpoint to get summary of user's data (for display before deletion).
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with user data summary
    """
    user = request.user
    
    # Get detailed counts
    sent_messages = Message.objects.filter(sender=user)
    received_messages = Message.objects.filter(receiver=user)
    notifications = user.notifications.all()
    message_edits = MessageHistory.objects.filter(edited_by=user)
    
    data = {
        'username': user.username,
        'email': user.email,
        'sent_messages_count': sent_messages.count(),
        'received_messages_count': received_messages.count(),
        'total_messages': sent_messages.count() + received_messages.count(),
        'notifications_count': notifications.count(),
        'unread_notifications_count': notifications.filter(is_read=False).count(),
        'message_edits_count': message_edits.count(),
        'account_created': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
    }
    
    return JsonResponse(data)