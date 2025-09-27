# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import Conversation, Message, User as CustomUser
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsOwnerOrParticipant, IsConversationParticipant
from .filters import MessageFilter, ConversationFilter
from .pagination import DefaultPagination


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    Provides CRUD operations and conversation-specific actions.
    """
    serializer_class = ConversationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ConversationFilter
    pagination_class = DefaultPagination
    search_fields = ['participants__email', 'participants__first_name', 'participants__last_name']
    permission_classes = [permissions.IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        """Restrict conversations to only those the user participates in."""
        user = self.request.user
        return Conversation.objects.filter(participants=user).distinct()
    
    def get_object(self):
        """Ensure object-level access only for participants."""
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        """Create a new conversation with participants."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
            user = CustomUser.objects.get(user_id=user_id)
            conversation.participants.add(user)
            return Response({'message': 'Participant added successfully'})
        except CustomUser.DoesNotExist:
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
            user = CustomUser.objects.get(user_id=user_id)
            
            # Prevent removing the last participant
            if conversation.participants.count() <= 1:
                return Response(
                    {'error': 'Cannot remove the last participant'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.remove(user)
            return Response({'message': 'Participant removed successfully'})
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    Provides CRUD operations and message-specific actions.
    """
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = MessageFilter
    pagination_class = DefaultPagination
    search_fields = ['sender__email', 'message_body', 'conversation__conversation_id']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrParticipant]
    
    def get_queryset(self):
        """Restrict messages to only those in conversations the user participates in."""
        user = self.request.user
        queryset = Message.objects.filter(conversation__participants=user).distinct()

        # If nested under a conversation, filter further
        conversation_pk = self.kwargs.get('conversation_pk')
        if conversation_pk:
            # Ensure user is a participant of this conversation
            if not Conversation.objects.filter(
                conversation_id=conversation_pk, 
                participants=user
            ).exists():
                raise PermissionDenied("You are not a participant in this conversation.")
            queryset = queryset.filter(conversation__conversation_id=conversation_pk)

        return queryset
    
    def perform_update(self, serializer):
        """Only sender can update their own message."""
        message = self.get_object()
        if message.sender != self.request.user:
            raise PermissionDenied("You cannot edit someone else's message.")
        serializer.save()

    def perform_destroy(self, instance):
        """Only sender can delete their own message."""
        if instance.sender != self.request.user:
            raise PermissionDenied("You cannot delete someone else's message.")
        instance.delete()

    def create(self, request, *args, **kwargs):
        """Send a message to an existing conversation."""
        # Check if we're accessing via nested route
        conversation_pk = self.kwargs.get('conversation_pk') or request.data.get('conversation')

        if not conversation_pk:
            return Response(
                {"error": "Conversation ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        message_body = request.data.get('message_body')
        message_type = request.data.get('message_type', 'text')
        
        if not message_body:
            return Response(
                {"error": "message_body is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resolve conversation
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_pk)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Invalid conversation ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Sender is always the logged-in user
        sender = request.user
        
        # Verify sender is a participant in the conversation
        if not conversation.participants.filter(user_id=sender.user_id).exists():
            return Response(
                {"error": "Sender is not a participant in this conversation."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        message = Message.objects.create(
            sender=sender,
            conversation=conversation,
            message_body=message_body,
            message_type=message_type,
        )
        
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read by the authenticated user."""
        message = self.get_object()
        user = request.user

        # Prevent marking own messages
        if message.sender == user:
            return Response(
                {'error': 'Cannot mark your own message as read'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For now: simple global flag (could be extended to per-user read receipts)
        message.is_read = True
        message.save()
        
        return Response({'message': 'Message marked as read'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages for the authenticated user only."""
        user = request.user
        
        unread_messages = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).order_by('-sent_at').distinct()
        
        serializer = MessageSerializer(unread_messages, many=True)
        return Response({
            'messages': serializer.data,
            'count': unread_messages.count()
        })


