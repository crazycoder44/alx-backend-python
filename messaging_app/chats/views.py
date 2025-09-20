from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.db import transaction
from django.utils import timezone
from .models import User, Conversation, Message, MessageReadStatus
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer,
    ConversationListSerializer, ConversationDetailSerializer, 
    ConversationCreateSerializer, ConversationWithRecentMessagesSerializer,
    MessageSerializer, MessageDetailSerializer, MessageReadStatusSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    Provides CRUD operations and user-specific actions.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Allow registration without authentication."""
        if self.action == 'create':
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's profile."""
        serializer = UserDetailSerializer(
            request.user, 
            data=request.data, 
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users by name or email."""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response(
                {'error': 'Query must be at least 2 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:20]
        
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    Provides full CRUD operations and conversation-specific actions.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return conversations where user is a participant."""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            Prefetch('messages', queryset=Message.objects.select_related('sender'))
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        elif self.action == 'list':
            return ConversationListSerializer
        elif self.action in ['recent_messages', 'load_messages']:
            return ConversationWithRecentMessagesSerializer
        return ConversationDetailSerializer
    
    def perform_create(self, serializer):
        """Create conversation and ensure current user is a participant."""
        with transaction.atomic():
            conversation = serializer.save()
            # Always add the creator as a participant
            conversation.participants.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            conversation.participants.add(user)
            
            # Create a system message about the addition
            Message.objects.create(
                sender=request.user,
                conversation=conversation,
                message_body=f"{user.full_name} was added to the conversation",
                message_type='system'
            )
            
            return Response({'message': 'Participant added successfully'})
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            
            # Prevent removing the last participant
            if conversation.participants.count() <= 1:
                return Response(
                    {'error': 'Cannot remove the last participant'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.remove(user)
            
            # Create a system message about the removal
            Message.objects.create(
                sender=request.user,
                conversation=conversation,
                message_body=f"{user.full_name} was removed from the conversation",
                message_type='system'
            )
            
            return Response({'message': 'Participant removed successfully'})
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Allow user to leave the conversation."""
        conversation = self.get_object()
        
        if conversation.participants.count() <= 1:
            # If user is the last participant, mark conversation as inactive
            conversation.is_active = False
            conversation.save()
        else:
            conversation.participants.remove(request.user)
            
            # Create a system message about leaving
            Message.objects.create(
                sender=request.user,
                conversation=conversation,
                message_body=f"{request.user.full_name} left the conversation",
                message_type='system'
            )
        
        return Response({'message': 'Left conversation successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark all messages in conversation as read for current user."""
        conversation = self.get_object()
        
        # Get unread messages for this user
        unread_messages = conversation.messages.exclude(
            sender=request.user
        ).exclude(
            read_statuses__user=request.user
        )
        
        # Create read status entries
        read_statuses = [
            MessageReadStatus(message=message, user=request.user)
            for message in unread_messages
        ]
        
        MessageReadStatus.objects.bulk_create(read_statuses, ignore_conflicts=True)
        
        return Response({
            'message': f'Marked {len(read_statuses)} messages as read'
        })
    
    @action(detail=True, methods=['get'])
    def recent_messages(self, request, pk=None):
        """Get recent messages in the conversation."""
        conversation = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        messages = conversation.messages.select_related('sender').order_by('-sent_at')[offset:offset+limit]
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        return Response({
            'messages': serializer.data,
            'has_more': conversation.messages.count() > offset + limit
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search conversations by title or participant name."""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response(
                {'error': 'Query must be at least 2 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversations = self.get_queryset().filter(
            Q(title__icontains=query) |
            Q(participants__first_name__icontains=query) |
            Q(participants__last_name__icontains=query) |
            Q(participants__username__icontains=query)
        ).distinct()
        
        serializer = ConversationListSerializer(
            conversations, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    Provides full CRUD operations and message-specific actions.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return messages from conversations where user is a participant."""
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('sender', 'conversation').prefetch_related(
            'conversation__participants'
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return MessageDetailSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        """Set sender to current user and validate conversation access."""
        conversation_id = serializer.validated_data.get('conversation').conversation_id
        conversation = get_object_or_404(
            Conversation, 
            conversation_id=conversation_id,
            participants=self.request.user
        )
        
        serializer.save(sender=self.request.user, conversation=conversation)
    
    def create(self, request, *args, **kwargs):
        """Create a new message and handle real-time updates."""
        # Add sender_id to the data automatically
        request.data['sender_id'] = request.user.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save()
        
        # Update conversation's updated_at timestamp
        message.conversation.updated_at = timezone.now()
        message.conversation.save(update_fields=['updated_at'])
        
        # Return the created message with full details
        response_serializer = MessageDetailSerializer(
            message, 
            context={'request': request}
        )
        
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific message as read."""
        message = self.get_object()
        
        # Don't allow marking own messages as read
        if message.sender == request.user:
            return Response(
                {'error': 'Cannot mark your own message as read'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        read_status, created = MessageReadStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        if created:
            return Response({'message': 'Message marked as read'})
        else:
            return Response({'message': 'Message was already read'})
    
    @action(detail=True, methods=['get'])
    def read_status(self, request, pk=None):
        """Get read status information for a message."""
        message = self.get_object()
        read_statuses = MessageReadStatus.objects.filter(
            message=message
        ).select_related('user')
        
        serializer = MessageReadStatusSerializer(
            read_statuses, 
            many=True, 
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread messages for the current user."""
        unread_messages = self.get_queryset().exclude(
            sender=request.user
        ).exclude(
            read_statuses__user=request.user
        ).order_by('-sent_at')
        
        # Optional conversation filtering
        conversation_id = request.query_params.get('conversation_id')
        if conversation_id:
            unread_messages = unread_messages.filter(
                conversation__conversation_id=conversation_id
            )
        
        serializer = MessageSerializer(
            unread_messages, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'messages': serializer.data,
            'count': unread_messages.count()
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search messages by content."""
        query = request.query_params.get('q', '')
        if len(query) < 3:
            return Response(
                {'error': 'Query must be at least 3 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(
            message_body__icontains=query
        ).order_by('-sent_at')[:50]
        
        # Optional conversation filtering
        conversation_id = request.query_params.get('conversation_id')
        if conversation_id:
            messages = messages.filter(
                conversation__conversation_id=conversation_id
            )
        
        serializer = MessageSerializer(
            messages, 
            many=True, 
            context={'request': request}
        )
        
        return Response(serializer.data)


# URL Configuration (urls.py)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]

# This will create the following endpoints:

# User endpoints:
# GET    /api/v1/users/                    - List users
# POST   /api/v1/users/                    - Create user (register)
# GET    /api/v1/users/{id}/               - Get user details
# PUT    /api/v1/users/{id}/               - Update user
# DELETE /api/v1/users/{id}/               - Delete user
# GET    /api/v1/users/me/                 - Get current user profile
# PUT    /api/v1/users/update_profile/     - Update current user profile
# GET    /api/v1/users/search/?q=query     - Search users

# Conversation endpoints:
# GET    /api/v1/conversations/                           - List user's conversations
# POST   /api/v1/conversations/                           - Create new conversation
# GET    /api/v1/conversations/{id}/                      - Get conversation details
# PUT    /api/v1/conversations/{id}/                      - Update conversation
# DELETE /api/v1/conversations/{id}/                      - Delete conversation
# POST   /api/v1/conversations/{id}/add_participant/      - Add participant
# POST   /api/v1/conversations/{id}/remove_participant/   - Remove participant
# POST   /api/v1/conversations/{id}/leave/                - Leave conversation
# POST   /api/v1/conversations/{id}/mark_read/            - Mark all messages as read
# GET    /api/v1/conversations/{id}/recent_messages/      - Get recent messages
# GET    /api/v1/conversations/search/?q=query            - Search conversations

# Message endpoints:
# GET    /api/v1/messages/                        - List user's messages
# POST   /api/v1/messages/                        - Send new message
# GET    /api/v1/messages/{id}/                   - Get message details
# PUT    /api/v1/messages/{id}/                   - Update message
# DELETE /api/v1/messages/{id}/                  - Delete message
# POST   /api/v1/messages/{id}/mark_read/         - Mark message as read
# GET    /api/v1/messages/{id}/read_status/       - Get message read status
# GET    /api/v1/messages/unread/                 - Get unread messages
# GET    /api/v1/messages/search/?q=query         - Search messages
"""