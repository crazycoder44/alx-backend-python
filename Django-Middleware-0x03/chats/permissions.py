# messaging_app/chats/permissions.py

from rest_framework import permissions
from django.db.models import Q
from .models import Conversation, Message


class IsOwnerOrParticipant(permissions.BasePermission):
    """
    Custom permission to only allow users to access their own messages
    and conversations they participate in.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated for any request.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission to only allow users to access objects
        they own or participate in.
        """
        # For Message objects
        if isinstance(obj, Message):
            # User can access message if they're the sender or participant in the conversation
            return (obj.sender == request.user or 
                   obj.conversation.participants.filter(user_id=request.user.user_id).exists())
        
        # For Conversation objects
        elif isinstance(obj, Conversation):
            # User can access conversation if they're a participant
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        # For other objects, deny by default
        return False


class IsMessageSender(permissions.BasePermission):
    """
    Custom permission to only allow message senders to edit/delete their messages.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Only allow message sender to modify the message.
        """
        if isinstance(obj, Message):
            # Only sender can edit/delete message
            if request.method in ["PUT", "PATCH", "DELETE"]:
                return obj.sender == request.user
            # Anyone in conversation can read
            elif request.method in permissions.SAFE_METHODS:
                return (obj.sender == request.user or 
                        obj.conversation.participants.filter(user_id=request.user.user_id).exists())
        
        return False


class IsConversationParticipant(permissions.BasePermission):
    """
    Custom permission for conversation-specific operations.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation.
        """
        if isinstance(obj, Conversation):
            is_participant = obj.participants.filter(user_id=request.user.user_id).exists()
            
            # For read operations, participant access is enough
            if view.action in ['retrieve', 'list']:
                return is_participant
            
            # For add/remove participant operations, any participant can do it
            # (you might want to restrict this to admins or conversation creators)
            elif view.action in ['add_participant', 'remove_participant']:
                return is_participant
            
            # For update/delete, you might want only conversation creator
            # For now, allowing any participant
            elif view.action in ['update', 'partial_update', 'destroy']:
                return is_participant
        
        return False


class CanMarkAsRead(permissions.BasePermission):
    """
    Permission to mark messages as read - only recipients can mark messages as read.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Only message recipients (conversation participants except sender) can mark as read.
        """
        if isinstance(obj, Message) and view.action == 'mark_read':
            # User must be in conversation but not be the sender
            return (obj.conversation.participants.filter(user_id=request.user.user_id).exists() 
                   and obj.sender != request.user)
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Others can only read if they have access.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request if user has basic access
        if request.method in permissions.SAFE_METHODS:
            if isinstance(obj, Message):
                return (obj.sender == request.user or 
                       obj.conversation.participants.filter(user_id=request.user.user_id).exists())
            elif isinstance(obj, Conversation):
                return obj.participants.filter(user_id=request.user.user_id).exists()
        
        # Write permissions are only allowed to the owner of the object
        if isinstance(obj, Message):
            return obj.sender == request.user
        elif isinstance(obj, Conversation):
            # For conversations, you might want to check for a creator field
            # For now, allowing any participant to modify
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        return False


class UnreadMessagesPermission(permissions.BasePermission):
    """
    Permission for accessing unread messages - users can only see their own unread messages.
    """
    
    def has_permission(self, request, view):
        """
        Only authenticated users can access unread messages endpoint.
        """
        return request.user and request.user.is_authenticated


# Utility function to check if user can access conversation
def user_can_access_conversation(user, conversation):
    """
    Utility function to check if a user can access a conversation.
    """
    return conversation.participants.filter(user_id=user.user_id).exists()


# Utility function to check if user can access message
def user_can_access_message(user, message):
    """
    Utility function to check if a user can access a message.
    """
    return (message.sender == user or 
            message.conversation.participants.filter(user_id=user.user_id).exists())


# Custom queryset filters
class UserAccessibleQuerysetMixin:
    """
    Mixin to filter querysets to only include objects the user can access.
    """
    
    def get_user_conversations(self, user):
        """
        Get conversations that the user participates in.
        """
        return Conversation.objects.filter(participants=user)
    
    def get_user_messages(self, user):
        """
        Get messages that the user can access (sent by them or in their conversations).
        """
        return Message.objects.filter(
            Q(sender=user) | Q(conversation__participants=user)
        ).distinct()
    
    def get_user_unread_messages(self, user):
        """
        Get unread messages for the user (excluding their own sent messages).
        """
        return Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).distinct()